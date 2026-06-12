import os
import json
from agents.base_agent import BaseAgent
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class HiringSimulationAgent(BaseAgent):
    def __init__(self):
        super().__init__("Hiring Simulation Agent")
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    def run(self, state: dict):
        self.log(state, "Starting hiring simulation...")

        prompt = f"""
You are simulating a complete hiring process for a {state['target_role']} position.

Candidate Profile:
- Skills: {', '.join(state['resume_skills'])}
- Missing Skills: {', '.join(state['missing_skills'])}
- Experience Level: {state['level']}
- Match Score: {state['match_score']}%

Simulate 4 hiring stages. Each stage evaluates the candidate independently.

Return ONLY a valid JSON object with exactly this structure, nothing else:
{{
    "ats": {{
        "score": <0-100>,
        "verdict": "<one line verdict>",
        "concerns": ["concern 1", "concern 2", "concern 3"]
    }},
    "recruiter": {{
        "score": <0-100>,
        "verdict": "<one line verdict>",
        "concerns": ["concern 1", "concern 2", "concern 3"]
    }},
    "hiring_manager": {{
        "score": <0-100>,
        "verdict": "<one line verdict>",
        "concerns": ["concern 1", "concern 2", "concern 3"]
    }},
    "technical_panel": {{
        "score": <0-100>,
        "verdict": "<one line verdict>",
        "concerns": ["concern 1", "concern 2", "concern 3"]
    }},
    "final_verdict": {{
        "decision": "<Hire / Strong Maybe / Maybe / Reject>",
        "confidence": <0-100>,
        "reasoning": "<2-3 sentences explaining the final decision>",
        "shortlisting_probability": <0-100>
    }}
}}

Guidelines:
- ATS Agent: Focus on keyword matching, required skills presence, format
- Recruiter Agent: Focus on overall profile, experience level, career progression
- Hiring Manager Agent: Focus on role fit, leadership potential, project quality
- Technical Panel Agent: Focus on technical depth, missing critical skills, deployment readiness
- Final Verdict: Aggregate all 4 scores into a realistic hiring decision
"""

        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1500
            )

            raw = response.choices[0].message.content.strip()

            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0].strip()

            result = json.loads(raw)

            state["hiring_simulation"] = {
                "ats": result.get("ats", {}),
                "recruiter": result.get("recruiter", {}),
                "hiring_manager": result.get("hiring_manager", {}),
                "technical_panel": result.get("technical_panel", {}),
                "final_verdict": result.get("final_verdict", {})
            }

            state["shortlisting_probability"] = result.get("final_verdict", {}).get("shortlisting_probability", 0)

            decision = result.get("final_verdict", {}).get("decision", "")
            self.log(state, f"Simulation complete — Final verdict: {decision}")

        except Exception as e:
            self.log(state, f"Error: {str(e)}")
            state["hiring_simulation"] = {
                "ats": {"score": 0, "verdict": "Unavailable", "concerns": []},
                "recruiter": {"score": 0, "verdict": "Unavailable", "concerns": []},
                "hiring_manager": {"score": 0, "verdict": "Unavailable", "concerns": []},
                "technical_panel": {"score": 0, "verdict": "Unavailable", "concerns": []},
                "final_verdict": {
                    "decision": "Unavailable",
                    "confidence": 0,
                    "reasoning": "Simulation unavailable at this time.",
                    "shortlisting_probability": 0
                }
            }

        return state