import json
import os

from dotenv import load_dotenv
from groq import Groq, GroqError

from agents.base_agent import BaseAgent


STAGES = ("ats", "recruiter", "hiring_manager", "technical_panel")
SKILL_LABELS = {"python": "Python", "javascript": "JavaScript", "typescript": "TypeScript",
                "power bi": "Power BI", "git": "Git", "sql": "SQL", "mlops": "MLOps",
                "aws": "AWS", "html": "HTML", "css": "CSS", "r": "R", "go": "Go"}

NO_REQUIREMENTS = {
    "ats": (
        "No supported skill terms were detected in the job description.",
        "Try the built-in role checklist or paste the section listing required skills.",
    ),
    "recruiter": (
        "The extracted requirements give a recruiter little to compare with the resume.",
        "Identify one explicit requirement in the posting and match it to a real accomplishment.",
    ),
    "hiring_manager": (
        "The extracted requirements provide no specific skill to connect to a project.",
        "Pick one responsibility from the posting and prepare an example of similar work.",
    ),
    "technical_panel": (
        "The extracted requirements provide no skill to use as an interview topic.",
        "Choose a tool named in the posting and prepare to explain how you would use it.",
    ),
}


class HiringSimulationAgent(BaseAgent):
    """Build practice feedback tied to the deterministic skill analysis."""

    def __init__(self, enabled=True):
        super().__init__("Hiring Simulation Agent")
        load_dotenv()
        api_key = os.getenv("GROQ_API_KEY", "").strip()
        self.client = Groq(api_key=api_key, timeout=12, max_retries=0) if enabled and api_key else None

    def run(self, state: dict):
        review = self._build_review(state)
        review["source"] = "rules"
        if self.client and state["jd_skills"]:
            try:
                actions = self._suggest_actions(state, review)
            except (GroqError, ValueError, TypeError, AttributeError, IndexError):
                self.log(state, "AI suggestions unavailable. Used practice checklist actions.")
            else:
                for stage in STAGES:
                    review[stage]["action"] = actions[stage].strip()
                review["source"] = "ai"

        state["hiring_simulation"] = review
        self.log(state, "Prepared four evidence-based practice reviews")
        return state

    @staticmethod
    def _build_review(state):
        requirements = state["jd_skills"]
        if not requirements:
            return {
                stage: {"concern": concern, "action": action, "evidence": []}
                for stage, (concern, action) in NO_REQUIREMENTS.items()
            }

        matched = state["matched_skills"]
        gaps = state["missing_skills"]
        ats = (gaps or matched)[0]
        recruiter = (matched or gaps)[0]
        manager = (gaps or matched)[-1]
        technical = (matched or gaps)[-1]

        ats_label = SKILL_LABELS.get(ats, ats)
        recruiter_label = SKILL_LABELS.get(recruiter, recruiter)
        manager_label = SKILL_LABELS.get(manager, manager)
        technical_label = SKILL_LABELS.get(technical, technical)

        feedback = {
            "ats": (
                ats,
                f"The extracted resume shows no evidence for {ats_label}, one of the recognized requirements."
                if ats in gaps else
                f"All {len(requirements)} recognized requirements appear in the extracted resume.",
                f"Check that your resume uses the posting's wording for {ats_label} wherever it accurately describes your experience.",
            ),
            "recruiter": (
                recruiter,
                f"A recruiter may ask how your work with {recruiter_label} relates to this role."
                if recruiter in matched else
                f"The resume provides no extracted evidence for {recruiter_label}.",
                f"Prepare a short example of how you used {recruiter_label}, if you have one, including the result.",
            ),
            "hiring_manager": (
                manager,
                f"A hiring manager may ask which outcome your work with {manager_label} supported."
                if manager in matched else
                f"The extracted resume has no project evidence for the {manager_label} requirement.",
                f"Prepare one project example for {manager_label} that explains what you owned and what changed."
                if manager in matched else
                f"Build a small sample project with {manager_label} and document what you learned.",
            ),
            "technical_panel": (
                technical,
                f"A technical panel may ask you to explain a trade-off you made using {technical_label}."
                if technical in matched else
                f"The resume provides no extracted evidence of hands-on work with {technical_label}.",
                f"Practice explaining one decision involving {technical_label}, an alternative, and how you would test the result.",
            ),
        }

        review = {}
        for stage, (skill, concern, action) in feedback.items():
            evidence = []
            resume_line = state["skill_evidence"].get(skill)
            if resume_line:
                evidence.append({"source": "resume", "skill": skill, "line": resume_line})
            requirement_line = state["requirement_evidence"].get(skill)
            if requirement_line:
                evidence.append({"source": "requirements", "skill": skill, "line": requirement_line})
            elif state["jd_source"] == "role_based":
                evidence.append({
                    "source": "role",
                    "skill": skill,
                    "line": f"{skill} is on the built-in {state['target_role']} checklist.",
                })
            review[stage] = {"concern": concern, "action": action, "evidence": evidence}
        return review

    def _suggest_actions(self, state, review):
        # The provider only needs the role and skill-level context to suggest actions.
        practice_context = {
            "role": state["target_role"],
            "stages": {
                stage: {
                    "skill": review[stage]["evidence"][0]["skill"],
                    "present": review[stage]["evidence"][0]["source"] == "resume",
                }
                for stage in STAGES
                if review[stage]["evidence"]
            },
        }
        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Suggest one concrete practice action per hiring stage. Return a JSON object with exactly "
                        "the keys ats, recruiter, hiring_manager, technical_panel. Each value must be one plain "
                        "sentence naming the supplied skill. ATS should focus on accurate wording, recruiter on "
                        "a concise example, hiring_manager on an outcome, and technical_panel on a technical "
                        "decision. For missing evidence, suggest practice or asking the candidate to confirm their "
                        "experience. Never assume experience, prescribe fabricated claims, or give hiring odds."
                    ),
                },
                {"role": "user", "content": json.dumps(practice_context)},
            ],
            temperature=0.2,
            max_tokens=400,
        )
        result = json.loads(response.choices[0].message.content)
        if not isinstance(result, dict) or any(
            not isinstance(result.get(stage), str)
            or not 1 <= len(result[stage].strip()) <= 260
            for stage in STAGES
        ):
            raise ValueError("Invalid practice actions")
        return result
