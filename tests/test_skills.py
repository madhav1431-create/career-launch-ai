import unittest
from io import BytesIO
from unittest.mock import patch

from core.orchestrator import Orchestrator
from engine import (
    classify_requirement_evidence,
    classify_resume_skill_evidence,
    detect_skill_evidence,
    detect_skills,
    extract_text_from_pdf,
)


def _positioned_pdf(*pages):
    """Build a tiny test PDF with exact line positions using the built-in PDF font."""
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    children = []
    for rows in pages:
        page_number = len(objects) + 1
        children.append(f"{page_number} 0 R")
        instructions = []
        for x, y, text in rows:
            text = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            instructions.append(f"BT /F1 11 Tf {x} {y} Td ({text}) Tj ET")
        stream = "\n".join(instructions).encode("ascii")
        objects.append((
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {page_number + 1} 0 R >>"
        ).encode("ascii"))
        objects.append(f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream")
    objects[1] = f"<< /Type /Pages /Count {len(children)} /Kids [{' '.join(children)}] >>".encode()

    pdf = BytesIO(b"%PDF-1.4\n")
    pdf.seek(0, 2)
    offsets = []
    for number, item in enumerate(objects, 1):
        offsets.append(pdf.tell())
        pdf.write(f"{number} 0 obj\n".encode() + item + b"\nendobj\n")
    startxref = pdf.tell()
    pdf.write(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    for offset in offsets:
        pdf.write(f"{offset:010d} 00000 n \n".encode())
    pdf.write(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{startxref}\n%%EOF".encode())
    pdf.seek(0)
    return pdf


class SkillDetectionTests(unittest.TestCase):
    def test_words_are_not_substring_matches(self):
        self.assertEqual(detect_skills("Built dashboards with JavaScript."), ["javascript"])
        self.assertEqual(detect_skills("Go live after the team reviews the report."), [])
        self.assertEqual(detect_skills("Maintained a GitHub repository."), ["github"])

    def test_aliases_and_punctuation_keep_original_evidence(self):
        line = "Used C++17, C#, sklearn, Postgres, K8s, and MLOps."
        evidence = detect_skill_evidence(f"Project experience\n{line}\nUsed C++ again.")
        self.assertEqual(
            evidence,
            dict.fromkeys(("c++", "c#", "scikit-learn", "postgresql", "kubernetes", "mlops"), line),
        )
        self.assertEqual(
            detect_skills("Stack: R, Golang, JS, NodeJS and RESTful APIs."),
            ["javascript", "r", "go", "node.js", "rest api"],
        )

    def test_wrapped_phrase_keeps_both_original_lines(self):
        text = "Project\nTrained a Machine\nLearning model."
        self.assertEqual(detect_skill_evidence(text), {"machine learning": "Trained a Machine\nLearning model."})

    def test_explicit_denials_are_separate_from_positive_evidence(self):
        denial = "No prior experience with Docker or Kubernetes."
        positive = "Built a dashboard with Docker."
        text = f"{denial}\n{positive}"
        found, denied = classify_resume_skill_evidence(text)
        self.assertEqual(found, {"docker": positive})
        self.assertEqual(denied, {"docker": denial, "kubernetes": denial})
        self.assertEqual(detect_skills(text), ["docker"])
        self.assertEqual(list(detect_skill_evidence(text, include_negated=True)), ["docker", "kubernetes"])

    def test_negation_does_not_spill_past_a_parenthesis_or_contrast(self):
        text = "Java (no professional experience), Python, and R. Never used Vue, but developed with React."
        found, denied = classify_resume_skill_evidence(text)
        self.assertEqual(set(found), {"python", "r", "react"})
        self.assertEqual(set(denied), {"java", "vue"})
        self.assertEqual(detect_skills("Not only Python but also Java."), ["python", "java"])

    def test_negation_applies_to_bare_and_wrapped_skill_lists(self):
        text = "No Docker or Kubernetes experience.\nI have never worked with\n    Vue."
        found, denied = classify_resume_skill_evidence(text)
        self.assertEqual(found, {})
        self.assertEqual(set(denied), {"docker", "kubernetes", "vue"})
        self.assertEqual(denied["vue"], "I have never worked with\nVue.")
        self.assertEqual(detect_skills("No SQL migration issues."), ["sql"])

    def test_negation_follows_wrapped_lists_and_stops_at_new_bullets(self):
        text = (
            "Never worked with\nDocker,\nJenkins,\nor Kubernetes.\n"
            "No paid work involving Terraform,\n- Built a Python CLI.\n"
            "Yet to write SQL, but used PostgreSQL for database administration."
        )
        found, denied = classify_resume_skill_evidence(text)
        self.assertEqual(set(found), {"python", "postgresql"})
        self.assertEqual(set(denied), {"docker", "kubernetes", "terraform", "sql"})
        self.assertEqual(denied["kubernetes"], "Never worked with\nDocker,\nJenkins,\nor Kubernetes.")

    def test_denial_section_stops_at_the_next_section(self):
        text = (
            "Tools I have not used:\n- Docker\n- Kubernetes\n"
            "Projects\n- Built a Vue application with TypeScript."
        )
        found, denied = classify_resume_skill_evidence(text)
        self.assertEqual(set(found), {"vue", "typescript"})
        self.assertEqual(set(denied), {"docker", "kubernetes"})
        self.assertEqual(denied["kubernetes"], "Tools I have not used:\n- Docker\n- Kubernetes")

    def test_group_suffix_does_not_negate_individual_parenthetical_neighbors(self):
        text = "Docker and Kubernetes: no hands-on\nexperience yet.\nPython, Java (no work experience)."
        found, denied = classify_resume_skill_evidence(text)
        self.assertEqual(set(found), {"python"})
        self.assertEqual(set(denied), {"docker", "java", "kubernetes"})

    def test_no_exposure_to_identifies_a_denial(self):
        text = "No professional exposure to Scala or Spark."
        found, denied = classify_resume_skill_evidence(text)
        self.assertEqual(found, {})
        self.assertEqual(denied, {"scala": text, "spark": text})


class PDFLayoutTests(unittest.TestCase):
    def test_columns_keep_wrapped_skills_and_denials_in_their_own_flow(self):
        with _positioned_pdf([
            (36, 740, "Built a Machine"), (352, 740, "Toolbox"),
            (36, 720, "Learning classifier."), (352, 720, "SQL"),
            (36, 700, "Never worked with"), (352, 700, "Python"),
            (36, 680, "Docker or Kubernetes."), (352, 680, "Git"),
        ]) as pdf:
            text = extract_text_from_pdf(pdf, preserve_case=True)
        self.assertIn("Docker or Kubernetes.\n\nToolbox\nSQL", text)
        found, denied = classify_resume_skill_evidence(text)
        self.assertEqual(found["machine learning"], "Built a Machine\nLearning classifier.")
        self.assertEqual(found["python"], "Python")
        self.assertEqual(denied["kubernetes"], "Never worked with\nDocker or Kubernetes.")
        self.assertEqual(set(found), {"machine learning", "sql", "python", "git"})

    def test_offset_columns_and_page_breaks_do_not_extend_a_denial(self):
        with _positioned_pdf([
            (36, 747, "Maintained Vue components."),
            (352, 739, "Technical Skills"),
            (36, 725, "No experience with Docker,"),
            (352, 717, "Python,"),
            (36, 703, "PostgreSQL, or Kafka."),
            (352, 695, "Never written SQL,"),
        ], [
            (36, 747, "Git"),
            (36, 725, "Shipped JavaScript fixes."),
        ]) as pdf:
            text = extract_text_from_pdf(pdf, preserve_case=True)
        self.assertIn("Kafka.\n\nTechnical Skills", text)
        self.assertIn("Never written SQL,\n\nGit", text)
        found, denied = classify_resume_skill_evidence(text)
        self.assertEqual(set(found), {"vue", "python", "git", "javascript"})
        self.assertEqual(set(denied), {"docker", "postgresql", "kafka", "sql"})

    def test_right_aligned_dates_keep_single_column_reading_order(self):
        with _positioned_pdf([
            (36, 740, "Data Assistant"), (405, 740, "June 2024 - Present"),
            (36, 720, "Built SQL reports."),
            (36, 700, "Reporting Intern"), (405, 700, "July 2023 - May 2024"),
            (36, 680, "Prepared Excel reports."),
        ]) as pdf:
            text = extract_text_from_pdf(pdf, preserve_case=True)
        self.assertEqual(text.splitlines(), [
            "Data Assistant June 2024 - Present", "Built SQL reports.",
            "Reporting Intern July 2023 - May 2024", "Prepared Excel reports.",
        ])


class RequirementPriorityTests(unittest.TestCase):
    def test_headings_and_inline_priority_keep_original_lines(self):
        required, preferred = classify_requirement_evidence(
            "Minimum Qualifications\n- Python\n- SQL\n\n"
            "Preferred Skills:\n- Docker\n- Kubernetes is mandatory\n"
            "Responsibilities: Build Tableau reports. AWS is a plus."
        )
        self.assertEqual(required, {
            "python": "- Python", "sql": "- SQL", "kubernetes": "- Kubernetes is mandatory",
            "tableau": "Responsibilities: Build Tableau reports. AWS is a plus.",
        })
        self.assertEqual(preferred, {
            "aws": "Responsibilities: Build Tableau reports. AWS is a plus.", "docker": "- Docker",
        })

    def test_mixed_inline_lists_and_duplicate_requirements(self):
        required, preferred = classify_requirement_evidence(
            "Required: Python and SQL, Docker preferred. SQL and Power BI are a plus."
        )
        self.assertEqual(set(required), {"python", "sql"})
        self.assertEqual(set(preferred), {"docker", "power bi"})


class RoleCoverageTests(unittest.TestCase):
    @patch("core.orchestrator.extract_text_from_pdf")
    def test_unrelated_skills_do_not_increase_coverage(self, extract_text):
        extract_text.return_value = "JavaScript, HTML, CSS, Git, React, Vue, TypeScript, Node.js, and Angular."
        state = Orchestrator().run("sample.pdf", "Required: Python and SQL.", "Data Scientist", include_ai=False)
        self.assertEqual(state["match_score"], 0)
        self.assertEqual(state["career_readiness_score"], 0)
        self.assertEqual(state["matched_skills"], [])
        self.assertEqual(state["missing_skills"], ["python", "sql"])
        self.assertNotIn("level", state)

    @patch("core.orchestrator.extract_text_from_pdf")
    def test_match_keeps_evidence_and_works_without_ai(self, extract_text):
        extract_text.return_value = "Queried production tables with SQL."
        jd_line = "Required: Python and SQL."
        state = Orchestrator().run("sample.pdf", jd_line, "Data Scientist", include_ai=False)
        self.assertEqual(state["matched_skills"], ["sql"])
        self.assertEqual(state["match_score"], 50)
        self.assertEqual(state["skill_evidence"], {"sql": "Queried production tables with SQL."})
        self.assertEqual(state["requirement_evidence"], {"python": jd_line, "sql": jd_line})
        self.assertTrue(state["project_recommendations"])
        self.assertTrue(state["interview_questions"]["technical"])
        self.assertFalse(state["ai_enabled"])

    @patch("core.orchestrator.extract_text_from_pdf", return_value="SQL\nNo experience with Python.\nTableau")
    def test_required_and_preferred_coverage_are_separate(self, _extract_text):
        state = Orchestrator().run(
            "sample.pdf", "Required: SQL and Python. Preferred: Docker and Tableau.", "Data Analyst",
            include_ai=False,
        )
        self.assertEqual(state["match_score"], 50)
        self.assertEqual(state["matched_skills"], ["sql"])
        self.assertEqual(state["missing_skills"], ["python"])
        self.assertEqual(state["preferred_match_score"], 50)
        self.assertEqual(state["matched_preferred_skills"], ["tableau"])
        self.assertEqual(state["missing_preferred_skills"], ["docker"])
        self.assertEqual([(step["skill"], step["priority"]) for step in state["roadmap"]],
                         [("python", "required"), ("docker", "preferred")])

    @patch("core.orchestrator.extract_text_from_pdf", return_value="Wrote SQL queries.")
    def test_review_recomputes_every_group_and_keeps_removed_evidence(self, _extract_text):
        pipeline = Orchestrator()
        preview = pipeline.preview("sample.pdf", "SQL and Python required. Docker preferred.", "Data Analyst")
        review = {"resume_skills": ["python"], "required_skills": ["sql"], "preferred_skills": ["python"]}
        state = pipeline.analyze(preview, include_ai=False, review=review)
        self.assertTrue(state["review_applied"])
        self.assertEqual(state["match_score"], 0)
        self.assertEqual(state["preferred_match_score"], 100)
        self.assertEqual(state["missing_skills"], ["sql"])
        self.assertEqual(state["skill_evidence"], {})
        self.assertEqual(state["excluded_skill_evidence"], {"sql": "Wrote SQL queries."})
        self.assertEqual(preview["resume_skills"], ["sql"])
        self.assertEqual(preview["interview_questions"], {"technical": [], "behavioral": [], "project": []})

    @patch("core.orchestrator.extract_text_from_pdf", return_value="Built Tableau reports.")
    def test_preferred_only_posting_has_working_practice_feedback(self, _extract_text):
        state = Orchestrator().run("sample.pdf", "Preferred: Tableau", "Data Analyst", include_ai=False)
        self.assertEqual(state["required_skills"], [])
        self.assertEqual(state["match_score"], 0)
        self.assertEqual(state["preferred_match_score"], 100)
        self.assertIn("preferred skills", state["hiring_simulation"]["ats"]["concern"])

    @patch("core.orchestrator.extract_text_from_pdf", return_value="Wrote SQL queries.")
    def test_practice_distinguishes_manual_requirements_from_role_checklist(self, _extract_text):
        review = {"resume_skills": ["sql"], "required_skills": ["docker", "sql"], "preferred_skills": []}
        state = Orchestrator().run("sample.pdf", "", "Data Analyst", include_ai=False, review=review)
        simulation = state["hiring_simulation"]
        self.assertEqual(simulation["ats"]["evidence"], [{
            "source": "review", "skill": "docker", "line": "Added as a target skill during review.",
        }])
        self.assertIn(
            {"source": "role", "skill": "sql", "line": "sql is on the built-in Data Analyst checklist."},
            simulation["recruiter"]["evidence"],
        )


if __name__ == "__main__":
    unittest.main()
