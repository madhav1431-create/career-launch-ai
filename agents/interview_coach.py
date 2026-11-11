import json

from groq import Groq

from agents.base_agent import BaseAgent


class InterviewCoachAgent(BaseAgent):
    def __init__(self, *, api_key=""):
        super().__init__("Interview Coach Agent")
        self.client = Groq(api_key=api_key, timeout=12.0, max_retries=0) if api_key else None

    def run(self, state: dict):
        if self.client is None:
            return self._use_fallback(state)

        self.log(state, "Preparing interview questions...")

        prompt = f"""
You are an expert technical interviewer. Generate interview questions for the following candidate.

Target Role: {state['target_role']}
Skills Mentioned in the Resume: {', '.join(state['resume_skills'])}
Target Skills Without a Resume Match: {', '.join(state['missing_skills'])}

Use the target role and skills to choose questions. Avoid assuming seniority or experience
the candidate has not described.

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

            questions = {
                "technical": result["technical_questions"],
                "behavioral": result["behavioral_questions"],
                "project": result["project_questions"],
            }
            if any(
                not isinstance(items, list) or any(not isinstance(item, dict) for item in items)
                for items in questions.values()
            ):
                raise ValueError("Unexpected interview question format")
            state["interview_questions"] = questions
            total = sum(len(items) for items in questions.values())
            self.log(state, f"Generated {total} interview questions")

        except Exception:
            return self._use_fallback(state)

        return state

    def _use_fallback(self, state):
        role = state["target_role"]
        skill = next(iter(state["matched_skills"] or state["jd_skills"]), "")
        questions = state["interview_questions"]

        if skill:
            questions["technical"] = [{
                "question": f"How would you use {skill} to solve a typical problem for a {role}?",
                "difficulty": "Medium",
                "tip": "Name the inputs, outline your approach, and explain how you would verify the result.",
            }]
        questions["behavioral"] = [{
            "question": "Tell me about a time you changed your approach after getting feedback.",
            "tip": "Describe the situation, what you changed, and what happened afterward.",
        }]
        questions["project"] = [{
            "question": f"Which project best shows how you would approach work as a {role}?",
            "tip": "Explain your contribution, one tradeoff you made, and how you evaluated the outcome.",
        }]
        self.log(state, "Prepared interview practice from the target skills")
        return state
