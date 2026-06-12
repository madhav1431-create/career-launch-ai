def create_state():
    return {
        "resume_text": "",
        "resume_skills": [],
        "jd_text": "",
        "jd_skills": [],
        "jd_source": "",
        "target_role": "",
        "match_score": 0,
        "level": "",
        "overview": "",
        "missing_skills": [],
        "roadmap": [],
        "project_recommendations": [],
        "certifications": [],
        "career_strategy": "",
        "interview_questions": [],
        "career_readiness_score": 0,
        "agent_logs": [],

        # Hiring Simulation
        "hiring_simulation": {
            "ats": {"score": 0, "verdict": "", "concerns": []},
            "recruiter": {"score": 0, "verdict": "", "concerns": []},
            "hiring_manager": {"score": 0, "verdict": "", "concerns": []},
            "technical_panel": {"score": 0, "verdict": "", "concerns": []},
            "final_verdict": {
                "decision": "",
                "confidence": 0,
                "reasoning": "",
                "shortlisting_probability": 0
            }
        },

        # Risk Assessment
        "risk_assessment": {
            "high_risks": [],
            "medium_risks": [],
            "low_risks": []
        },

        # Shortlisting Probability
        "shortlisting_probability": 0
    }