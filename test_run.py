from core.orchestrator import Orchestrator

# Test JD text — simulating a Data Scientist job description
test_jd = """
We are looking for a Data Scientist with strong skills in python, 
machine learning, deep learning, sql, statistics, pytorch, 
tensorflow, pandas, numpy and git.
Experience with docker and aws is a plus.
"""

# Using the sample resume already in your project
resume_path = "resume.pdf"

# Target role
target_role = "Data Scientist"

# Run the orchestrator
print("=" * 50)
print("   CareerLaunch AI — Agent Pipeline Test")
print("=" * 50)

orchestrator = Orchestrator()
state = orchestrator.run(resume_path, test_jd, target_role)

print("\n" + "=" * 50)
print("   RESULTS")
print("=" * 50)

print(f"\n Target Role     : {state['target_role']}")
print(f" Resume Skills   : {state['resume_skills']}")
print(f" JD Skills       : {state['jd_skills']}")
print(f" Match Score     : {state['match_score']}%")
print(f" Level           : {state['level']}")
print(f" Missing Skills  : {state['missing_skills']}")
print(f" Roadmap Steps   : {len(state['roadmap'])}")
print(f" Readiness Score : {state['career_readiness_score']}/100")

print("\n" + "=" * 50)
print("   AGENT LOGS")
print("=" * 50)
for log in state["agent_logs"]:
    print(f"[{log['time']}] {log['agent']} — {log['message']}")=