from io import BytesIO
import os
from unittest import TestCase
from unittest.mock import patch

from api import EXAMPLES, app
from core.orchestrator import Orchestrator


class AnalysisRoutesTest(TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.resume = (EXAMPLES / "demo_resume.pdf").read_bytes()
        no_key = patch.dict(os.environ, {"GROQ_API_KEY": ""})
        no_key.start()
        self.addCleanup(no_key.stop)

    def submit(self, **fields):
        return self.client.post("/analyze", data={
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

        def analyze(orchestrator, stream, *args):
            streams.append(stream)
            return original(orchestrator, stream, *args)

        original = Orchestrator.run
        with patch.object(Orchestrator, "run", new=analyze):
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
