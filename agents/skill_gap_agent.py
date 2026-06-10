from agents.base_agent import BaseAgent
from engine import compute_skill_gap

class SkillGapAgent(BaseAgent):
    def __init__(self):
        super().__init__("Skill Gap Agent")

    def run(self, state: dict):
        self.log(state, "Detecting skill gaps...")

        gap = compute_skill_gap(state["resume_skills"], state["jd_skills"])
        level = self._detect_level(state["resume_skills"])
        overview = self._generate_overview(
            state["target_role"],
            state["resume_skills"],
            state["jd_skills"],
            gap,
            level
        )

        state["missing_skills"] = gap
        state["overview"] = overview
        state["level"] = level

        self.log(state, f"Found {len(gap)} skill gaps | Level: {level}")
        return state

    def _detect_level(self, resume_skills):
        if len(resume_skills) > 8:
            return "Senior"
        elif len(resume_skills) > 4:
            return "Mid"
        else:
            return "Beginner"

    def _generate_overview(self, role, resume_skills, jd_skills, gap, level):
        matched = [s for s in jd_skills if s in resume_skills]

        # Role-specific context
        role_context = {
            "Data Scientist": "data analysis, machine learning, and statistical modeling",
            "ML Engineer": "building and deploying machine learning models at scale",
            "Data Analyst": "data visualization, SQL, and business intelligence",
            "Backend Developer": "server-side development, APIs, and database management",
            "AI Engineer": "designing and implementing AI systems and pipelines",
            "Frontend Developer": "building user interfaces and web applications"
        }

        role_desc = role_context.get(role, f"the {role} domain")

        if len(matched) == 0:
            strength_line = f"Your resume currently shows limited direct alignment with the {role} requirements."
        elif len(matched) <= 3:
            strength_line = f"You have foundational skills like {', '.join(matched[:3])} relevant to {role_desc}."
        else:
            strength_line = f"You bring strong relevant skills including {', '.join(matched[:5])} which directly apply to {role_desc}."

        if len(gap) == 0:
            gap_line = f"You appear well-prepared for the {role} role with no major skill gaps detected."
        elif len(gap) <= 3:
            gap_line = f"To fully qualify for this {role} position, focus on building {', '.join(gap[:3])}."
        else:
            gap_line = f"Key areas to develop for this {role} role include {', '.join(gap[:4])} among others."

        level_line = {
            "Senior": f"Your profile reflects a Senior-level background with {len(resume_skills)} detected skills.",
            "Mid": f"Your profile reflects a Mid-level background with {len(resume_skills)} detected skills.",
            "Beginner": f"Your profile reflects an entry-level background with room to grow in {role_desc}."
        }.get(level, "")

        return f"{level_line} {strength_line} {gap_line} With focused effort on the identified gaps, you can significantly strengthen your candidacy for this {role} position."