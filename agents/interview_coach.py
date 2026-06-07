import os
import json
from agents.base_agent import BaseAgent
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class InterviewCoachAgent(BaseAgent):
    def __init__(self):
        super().__init__("Interview Coach Agent")
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    def run(self, state: dict):
        self.log(state, "Preparing interview questions...")

        prompt = f"""
You are an expert technical interviewer. Generate interview questions for the following candidate.

Target Role: {state['target_role']}
Candidate Skills: {', '.join(state['resume_skills'])}
Missing Skills: {', '.join(state['missing_skills'])}
Experience Level: {state['level']}

Return ONLY a valid JSON object with exactly this structure, nothing else:
{{
    "technical_questions": [
        {{"question": "question text", "difficulty": "Easy/Medium/Hard", "tip": "what to focus on in answer"}},
        {{"question": "question text", "difficulty": "Easy/Medium/Hard", "tip": "what to focus on in answer"}},
        {{"question": "question text", "difficulty": "Easy/Medium/Hard", "tip": "what to focus on in answer"}},
        {{"question": "question text", "difficulty": "Easy/Medium/Hard", "tip": "what to focus on in answer"}},
        {{"question": "question text", "difficulty": "Easy/Medium/Hard", "tip": "what to focus on in answer"}}
    ],
    "behavioral_questions": [
        {{"question": "question text", "tip": "what to focus on in answer"}},
        {{"question": "question text", "tip": "what to focus on in answer"}},
        {{"question": "question text", "tip": "what to focus on in answer"}}
    ],
    "project_questions": [
        {{"question": "question text", "tip": "what to focus on in answer"}},
        {{"question": "question text", "tip": "what to focus on in answer"}}
    ]
}}
"""

        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1500
            )

            raw = response.choices[0].message.content.strip()

            # Clean response if it has markdown code blocks
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0].strip()

            result = json.loads(raw)

            state["interview_questions"] = {
                "technical": result.get("technical_questions", []),
                "behavioral": result.get("behavioral_questions", []),
                "project": result.get("project_questions", [])
            }

            total = (
                len(state["interview_questions"]["technical"]) +
                len(state["interview_questions"]["behavioral"]) +
                len(state["interview_questions"]["project"])
            )

            self.log(state, f"Generated {total} interview questions")

        except Exception as e:
            self.log(state, f"Error: {str(e)}")
            state["interview_questions"] = {
                "technical": [],
                "behavioral": [],
                "project": []
            }

        return state