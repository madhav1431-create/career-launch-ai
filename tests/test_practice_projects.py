from unittest import TestCase

from agents.practice_projects import practice_project
from api import app
from engine import skills


class PracticeProjectsTest(TestCase):
    def test_every_supported_skill_has_a_project_output_and_check(self):
        for skill in skills:
            with self.subTest(skill=skill):
                practice = practice_project(skill)
                self.assertEqual(set(practice), {"project", "output", "check"})
                self.assertTrue(all(text.strip() for text in practice.values()))

    def test_uncatalogued_skill_has_a_reproducible_exercise(self):
        practice = practice_project("a new tool")
        self.assertIn("a new tool", practice["project"])
        self.assertIn("two inputs", practice["output"])
        self.assertIn("both inputs", practice["check"])

    def test_demo_gaps_and_learning_steps_share_the_same_exercises(self):
        with app.test_client() as client:
            response = client.post("/demo")
        self.assertEqual(response.status_code, 200)
        result = response.get_json()
        roadmap = {step["skill"]: step["practice"] for step in result["roadmap"]}
        for gap in result["priority_gaps"]:
            self.assertEqual(gap["practice"], roadmap[gap["skill"]])
            self.assertEqual(gap["action"], gap["practice"]["project"])

        power_bi = roadmap["power bi"]
        self.assertIn("one-page Power BI dashboard", power_bi["project"])
        for item in ("order count", "total sales", "written takeaway"):
            self.assertIn(item, power_bi["output"])
        self.assertIn("reconcile both metrics", power_bi["check"])
