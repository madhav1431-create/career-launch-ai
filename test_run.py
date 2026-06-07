from core.orchestrator import Orchestrator

test_jd = """
We are looking for a Data Scientist with strong skills in python,
machine learning, deep learning, sql, statistics, pytorch,
tensorflow, pandas, numpy and git.
Experience with docker and aws is a plus.
"""

resume_path = "resume.pdf"
target_role = "Data Scientist"

print("=" * 50)
print("   CareerLaunch AI — Full 6-Agent Pipeline Test")
print("=" * 50)

orchestrator = Orchestrator()
state = orchestrator.run(resume_path, test_jd, target_role)

print("\n" + "=" * 50)
print("   RESULTS")
print("=" * 50)
print(f"\n Target Role      : {state['target_role']}")
print(f" Resume Skills    : {state['resume_skills']}")
print(f" Match Score      : {state['match_score']}%")
print(f" Level            : {state['level']}")
print(f" Missing Skills   : {state['missing_skills']}")
print(f" Roadmap Steps    : {len(state['roadmap'])}")
print(f" Readiness Score  : {state['career_readiness_score']}/100")

print("\n" + "=" * 50)
print("   CAREER STRATEGY")
print("=" * 50)
print(f"\n{state['career_strategy']}")

print("\n Projects Recommended:")
for p in state["project_recommendations"]:
    print(f"  - {p['name']}: {p['description']}")

print("\n Certifications:")
for c in state["certifications"]:
    print(f"  - {c['name']} by {c['provider']}")

print("\n" + "=" * 50)
print("   INTERVIEW QUESTIONS")
print("=" * 50)
print("\n Technical:")
for q in state["interview_questions"]["technical"]:
    print(f"  Q: {q['question']}")
    print(f"  Tip: {q['tip']}\n")

print(" Behavioral:")
for q in state["interview_questions"]["behavioral"]:
    print(f"  Q: {q['question']}\n")

print("\n" + "=" * 50)
print("   AGENT LOGS")
print("=" * 50)
for log in state["agent_logs"]:
    print(f"[{log['time']}] {log['agent']} — {log['message']}")