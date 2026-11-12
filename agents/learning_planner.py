from agents.base_agent import BaseAgent
from engine import skill_graph

class LearningPlannerAgent(BaseAgent):
    def __init__(self):
        super().__init__("Learning Planner Agent")

    def run(self, state: dict):
        self.log(state, "Generating learning roadmap...")

        missing = state["missing_skills"] + state["missing_preferred_skills"]
        roadmap = self._build_roadmap(missing)
        preferred = set(state["missing_preferred_skills"])
        for step in roadmap:
            step["priority"] = "preferred" if step["skill"] in preferred else "required"

        state["roadmap"] = roadmap
        self.log(state, f"Roadmap created with {len(roadmap)} steps")
        return state

    def _build_roadmap(self, missing_skills):
        ordered = []
        visited = set()

        def add_skill(skill):
            if skill in visited:
                return
            deps = skill_graph.get(skill, [])
            for dep in deps:
                if dep in missing_skills:
                    add_skill(dep)
            visited.add(skill)
            ordered.append(skill)

        for skill in missing_skills:
            add_skill(skill)

        roadmap = []
        for i, skill in enumerate(ordered):
            if skill in ["sql", "git", "html", "css", "linux"]:
                weeks = 2
            elif skill in ["python", "javascript", "react"]:
                weeks = 3
            else:
                weeks = 4

            roadmap.append({
                "step": i + 1,
                "skill": skill,
                "weeks": weeks
            })

        return roadmap
