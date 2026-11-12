from io import BytesIO
import json
import os
from pathlib import Path
import re
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from api import EXAMPLES, app
from core.orchestrator import Orchestrator
from scripts.build_demo import build_demo


class AnalysisRoutesTest(TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.resume = (EXAMPLES / "demo_resume.pdf").read_bytes()
        no_key = patch.dict(os.environ, {"GROQ_API_KEY": ""})
        no_key.start()
        self.addCleanup(no_key.stop)

    def submit(self, path="/analyze", **fields):
        return self.client.post(path, data={
            "resume": (BytesIO(self.resume), "candidate.pdf"),
            "target_role": "Data Analyst",
            **fields,
        })

    def test_demo_matches_role_requirements_without_a_provider(self):
        with self.client.get("/") as page:
            self.assertEqual(page.status_code, 200)
        response = self.client.post("/demo")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        result = response.get_json()
        self.assertTrue(result["demo"])
        self.assertFalse(result["ai_enabled"])
        self.assertEqual(set(result["matched_skills"]), {"sql", "python", "pandas", "git"})
        self.assertEqual(result["match_score"], 67)
        self.assertEqual(result["preferred_skills"], ["tableau"])
        self.assertEqual(result["preferred_match_score"], 100)
        self.assertEqual({gap["skill"] for gap in result["priority_gaps"]}, {"power bi", "statistics"})
        self.assertTrue(all(gap["requirement_line"] and gap["action"] for gap in result["priority_gaps"]))
        self.assertIn("Wrote SQL queries", result["skill_evidence"]["sql"])
        self.assertIn("Use SQL", result["requirement_evidence"]["sql"])
        self.assertNotIn("level", result)
        self.assertNotIn("shortlisting_probability", result)
        for stage in ("ats", "recruiter", "hiring_manager", "technical_panel"):
            review = result["hiring_simulation"][stage]
            self.assertTrue(review["concern"])
            self.assertTrue(review["evidence"])
            self.assertTrue(review["action"])

    def test_analysis_closes_its_resume_stream_even_when_processing_fails(self):
        streams = []

        def preview(orchestrator, stream, *args):
            streams.append(stream)
            return original(orchestrator, stream, *args)

        original = Orchestrator.preview
        with patch.object(Orchestrator, "preview", new=preview):
            response = self.submit(jd_text="Build reports with SQL.")
            self.assertEqual(response.status_code, 200)
            result = response.get_json()
            self.assertEqual(result["match_score"], 100)
            self.assertEqual(result["requirement_evidence"]["sql"], "Build reports with SQL.")
            self.assertTrue(streams[0].closed)

            self.resume = b"%PDF-invalid"
            response = self.submit()
            self.assertEqual(response.status_code, 400)
            self.assertIn("Resume", response.get_json()["error"])
            self.assertTrue(streams[1].closed)

    def test_rejects_identical_and_invalid_job_uploads(self):
        response = self.submit(jd_file=(BytesIO(self.resume), "same.pdf"))
        self.assertEqual(response.status_code, 400)
        self.assertIn("different PDF", response.get_json()["error"])
        response = self.submit(jd_file=(BytesIO(b"not a PDF"), "job.pdf"))
        self.assertEqual(response.status_code, 400)
        self.assertIn("Job description", response.get_json()["error"])

    def test_role_mode_keeps_the_source_clear(self):
        response = self.submit()
        self.assertEqual(response.status_code, 200)
        result = response.get_json()
        self.assertEqual(result["jd_source"], "role_based")
        self.assertEqual(result["requirement_evidence"], {})
        self.assertEqual(result["match_score"], result["career_readiness_score"])

    def test_preview_extracts_context_without_running_scoring(self):
        description = "Required: SQL and Python.\nPreferred: Docker."
        with patch.object(Orchestrator, "analyze", side_effect=AssertionError("Scored during review")):
            response = self.submit("/preview", jd_text=description)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        result = response.get_json()
        self.assertCountEqual(result["required_skills"], ["sql", "python"])
        self.assertEqual(result["preferred_skills"], ["docker"])
        self.assertIn("power bi", result["skill_catalog"])
        self.assertNotIn("match_score", result)

    def test_confirmed_edits_drive_scores_and_priority_actions(self):
        response = self.submit(
            jd_text="Required: SQL.\nPreferred: Power BI.",
            review=json.dumps({
                "resume_skills": ["power bi"],
                "required_skills": ["sql"],
                "preferred_skills": ["power bi"],
            }),
        )
        self.assertEqual(response.status_code, 200)
        result = response.get_json()
        self.assertTrue(result["review_applied"])
        self.assertEqual(result["match_score"], 0)
        self.assertEqual(result["preferred_match_score"], 100)
        gap, = result["priority_gaps"]
        self.assertEqual(gap["kind"], "required")
        self.assertEqual(gap["requirement_source"], "description")
        self.assertEqual(gap["resume_status"], "excluded")
        self.assertIn("Wrote SQL queries", gap["resume_line"])

    def test_rejects_overlapping_or_unknown_review_skills(self):
        review = {"resume_skills": ["sql"], "required_skills": ["sql"], "preferred_skills": ["sql"]}
        self.assertEqual(self.submit(review=json.dumps(review)).status_code, 400)
        review["preferred_skills"] = ["not a canonical skill"]
        self.assertEqual(self.submit(review=json.dumps(review)).status_code, 400)

    def test_static_export_contains_only_the_synthetic_analysis(self):
        with TemporaryDirectory() as folder:
            output_dir = Path(folder)
            build_demo(output_dir)
            self.assertEqual([path.name for path in output_dir.iterdir()], ["index.html"])
            html = (output_dir / "index.html").read_text(encoding="utf-8")
        payload = re.search(r'<script type="application/json" id="staticDemoData">(.*?)</script>', html)
        self.assertIsNotNone(payload)
        result = json.loads(payload[1])
        self.assertTrue(result["demo"])
        self.assertFalse(result["ai_enabled"])
        self.assertEqual(result["match_score"], 67)
