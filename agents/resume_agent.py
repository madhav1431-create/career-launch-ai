from agents.base_agent import BaseAgent
from engine import detect_skills

class ResumeAgent(BaseAgent):
    def __init__(self):
        super().__init__("Resume Intelligence Agent")

    def run(self, state: dict):
        self.log(state, "Starting resume analysis...")

        text = state["resume_text"]
        skills = detect_skills(text)

        state["resume_skills"] = skills

        self.log(state, f"Extracted {len(skills)} skills from resume")
        return state