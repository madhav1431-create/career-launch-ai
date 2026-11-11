import unittest
from unittest.mock import patch

from core.orchestrator import Orchestrator
from engine import detect_skill_evidence, detect_skills


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


if __name__ == "__main__":
    unittest.main()
