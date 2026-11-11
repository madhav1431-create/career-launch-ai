import json

from groq import Groq

from agents.base_agent import BaseAgent


class CareerStrategistAgent(BaseAgent):
    def __init__(self, *, api_key=""):
        super().__init__("Career Strategist Agent")
        self.client = Groq(api_key=api_key, timeout=12.0, max_retries=0) if api_key else None

    def run(self, state: dict):
        if self.client is None:
            return self._use_fallback(state)

        self.log(state, "Analyzing career profile...")

        prompt = f"""
You are an expert career strategist. Based on the following profile, provide career recommendations.

Target Role: {state['target_role']}
Skills Mentioned in the Resume: {', '.join(state['resume_skills'])}
Target Skills Without a Resume Match: {', '.join(state['missing_skills'])}

Return ONLY a valid JSON object with exactly this structure, nothing else:
{{
    "recommended_projects": [
        {{"name": "project name", "description": "2 sentence description", "skills_covered": ["skill1", "skill2"]}},
        {{"name": "project name", "description": "2 sentence description", "skills_covered": ["skill1", "skill2"]}},
        {{"name": "project name", "description": "2 sentence description", "skills_covered": ["skill1", "skill2"]}}
    ],
    "certifications": [
        {{"name": "cert name", "provider": "provider name", "relevance": "one line reason"}},
        {{"name": "cert name", "provider": "provider name", "relevance": "one line reason"}}
    ],
    "career_advice": "2-3 sentences of specific career advice for this person",
    "risk_assessment": {{
        "high_risks": ["risk 1", "risk 2"],
        "medium_risks": ["risk 1", "risk 2"],
        "low_risks": ["risk 1", "risk 2"]
    }}
}}

Use risk_assessment to prioritize gaps in resume evidence (max 3 items per category).
Avoid claims about seniority, hiring outcomes, or whether the candidate actually lacks a skill.
Use specific language like "Add a resume example that shows deployment experience".
"""

        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1200
            )

            raw = response.choices[0].message.content.strip()

            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0].strip()

            result = json.loads(raw)

            projects = result["recommended_projects"]
            certifications = result["certifications"]
            advice = result["career_advice"]
            risks = result["risk_assessment"]
            if (
                not isinstance(projects, list)
                or any(not isinstance(project, dict) for project in projects)
                or not isinstance(certifications, list)
                or any(not isinstance(certification, dict) for certification in certifications)
                or not isinstance(advice, str)
                or not isinstance(risks, dict)
                or any(not isinstance(items, list) for items in risks.values())
            ):
                raise ValueError("Unexpected career recommendation format")

            state["project_recommendations"] = projects
            state["certifications"] = certifications
            state["career_strategy"] = advice
            state["risk_assessment"] = risks

            self.log(state, f"Generated {len(state['project_recommendations'])} project recommendations")

        except Exception:
            return self._use_fallback(state)

        return state

    def _use_fallback(self, state):
        role = state["target_role"]
        if state["roadmap"]:
            skill = state["roadmap"][0]["skill"]
        else:
            skill = next(iter(state["matched_skills"]), "")

        if skill:
            state["project_recommendations"] = [{
                "name": f"{skill} practice project",
                "description": (
                    f"Choose a small task typical of a {role} and use {skill} to complete it. "
                    "Write a README explaining your approach, how to reproduce it, and how you checked the result."
                ),
                "skills_covered": [skill],
            }]
            state["career_strategy"] = (
                f"Prepare one concrete example of using {skill}. Describe what you built, "
                "the part you owned, and how you verified the outcome."
            )
        else:
            state["career_strategy"] = (
                "Start with a job description or role template that lists recognizable skills. "
                "Then choose one requirement to demonstrate in your resume."
            )

        self.log(state, "Prepared career guidance from the target skills")
        return state
