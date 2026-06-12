import os
import json
from agents.base_agent import BaseAgent
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class CareerStrategistAgent(BaseAgent):
    def __init__(self):
        super().__init__("Career Strategist Agent")
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    def run(self, state: dict):
        self.log(state, "Analyzing career profile...")

        prompt = f"""
You are an expert career strategist. Based on the following profile, provide career recommendations.

Target Role: {state['target_role']}
Current Skills: {', '.join(state['resume_skills'])}
Missing Skills: {', '.join(state['missing_skills'])}
Experience Level: {state['level']}

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

For risk_assessment:
- high_risks: Critical gaps that would likely cause rejection (max 3 items)
- medium_risks: Areas that need improvement but not dealbreakers (max 3 items)
- low_risks: Minor gaps that are easy to address (max 3 items)
Each risk should be a short specific statement like "No deployment experience" or "Weak SQL knowledge"
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

            state["project_recommendations"] = result.get("recommended_projects", [])
            state["certifications"] = result.get("certifications", [])
            state["career_strategy"] = result.get("career_advice", "")
            state["risk_assessment"] = result.get("risk_assessment", {
                "high_risks": [],
                "medium_risks": [],
                "low_risks": []
            })

            self.log(state, f"Generated {len(state['project_recommendations'])} project recommendations")

        except Exception as e:
            self.log(state, f"Error: {str(e)}")
            state["project_recommendations"] = []
            state["certifications"] = []
            state["career_strategy"] = "Career strategy unavailable at this time."
            state["risk_assessment"] = {
                "high_risks": [],
                "medium_risks": [],
                "low_risks": []
            }

        return state