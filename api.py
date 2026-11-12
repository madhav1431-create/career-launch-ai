from io import BytesIO
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.exceptions import RequestEntityTooLarge

from agents.practice_projects import practice_project
from core.orchestrator import Orchestrator
from engine import UnreadablePDFError, extract_text_from_pdf, role_skill_requirements, skills


load_dotenv()
ROOT = Path(__file__).resolve().parent
EXAMPLES = ROOT / "examples"
MAX_PDF_BYTES = 8 * 1024 * 1024
MAX_JOB_TEXT = 16_000
REVIEW_FIELDS = ("resume_skills", "required_skills", "preferred_skills")
SKILL_CATALOG = frozenset(skills)
PREVIEW_FIELDS = (
    "target_role", "jd_source", *REVIEW_FIELDS, "skill_evidence",
    "negated_skill_evidence", "requirement_evidence",
)
RESULT_FIELDS = (
    *PREVIEW_FIELDS, "jd_skills", "matched_skills", "match_score", "overview",
    "missing_skills", "matched_preferred_skills", "missing_preferred_skills",
    "preferred_match_score", "review_applied", "roadmap",
    "project_recommendations", "certifications",
    "career_strategy", "interview_questions", "career_readiness_score",
    "agent_logs", "hiring_simulation", "risk_assessment", "ai_enabled",
)
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 2 * MAX_PDF_BYTES + 64 * 1024
app.config["MAX_FORM_PARTS"] = 10
allowed_origins = [
    origin.strip()
    for origin in os.getenv("CAREERLAUNCH_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]
if allowed_origins:
    CORS(app, resources={r"/(?:analyze|preview)$": {"origins": allowed_origins}})


class InvalidUpload(ValueError):
    pass


def read_pdf_upload(upload, label):
    """Read one bounded upload into request-local memory."""
    data = upload.stream.read(MAX_PDF_BYTES + 1)
    if len(data) > MAX_PDF_BYTES:
        raise InvalidUpload(f"{label} must be 8 MB or smaller.")
    if not data.startswith(b"%PDF-"):
        raise InvalidUpload(f"{label} must be a PDF.")
    return data


def result_response(state, *, demo=False):
    return jsonify(
        success=True,
        demo=demo,
        priority_gaps=priority_gaps(state),
        **{key: state[key] for key in RESULT_FIELDS},
    )


def priority_gaps(state):
    """Show required gaps first and follow the roadmap within each group."""
    roadmap = {step["skill"]: step for step in state["roadmap"]}
    checklist = role_skill_requirements[state["target_role"]] if state["jd_source"] == "role_based" else ()
    gaps = []
    for kind, field in (("required", "missing_skills"), ("preferred", "missing_preferred_skills")):
        ordered = sorted(state[field], key=lambda skill: roadmap.get(skill, {}).get("step", float("inf")))
        for skill in ordered:
            negated = state["negated_skill_evidence"].get(skill)
            evidence = state["excluded_skill_evidence"].get(skill)
            requirement = state["requirement_evidence"].get(skill)
            practice = roadmap.get(skill, {}).get("practice") or practice_project(skill)
            gaps.append({
                "skill": skill,
                "kind": kind,
                "requirement_line": requirement,
                "requirement_source": "description" if requirement else "checklist" if skill in checklist else "review",
                "resume_line": evidence or negated,
                "resume_status": "excluded" if evidence else "negated" if negated else "missing",
                "action": practice["project"],
                "practice": practice,
            })
            if len(gaps) == 3:
                return gaps
    return gaps


def parse_review(raw):
    if raw is None:
        return None
    try:
        review = json.loads(raw)
    except (ValueError, RecursionError) as error:
        raise InvalidUpload("The skill review is invalid. Review the extracted skills again.") from error
    if not isinstance(review, dict) or set(review) != set(REVIEW_FIELDS):
        raise InvalidUpload("Confirm all three skill lists before scoring.")
    for field in REVIEW_FIELDS:
        values = review[field]
        if (
            not isinstance(values, list)
            or len(values) > len(SKILL_CATALOG)
            or any(not isinstance(skill, str) or skill not in SKILL_CATALOG for skill in values)
            or len(set(values)) != len(values)
        ):
            raise InvalidUpload("The skill review must contain supported skills with no duplicates.")
    if set(review["required_skills"]) & set(review["preferred_skills"]):
        raise InvalidUpload("A job skill can be required or preferred.")
    return review


@app.after_request
def set_response_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    if request.endpoint in {"preview", "analyze", "demo"}:
        response.headers["Cache-Control"] = "no-store"
    return response


@app.errorhandler(RequestEntityTooLarge)
def request_too_large(_error):
    return jsonify(error="Upload is too large. Use PDFs of 8 MB or smaller."), 413


@app.errorhandler(InvalidUpload)
def invalid_upload(error):
    return jsonify(error=str(error)), 400


@app.get("/")
def index():
    return send_from_directory(ROOT, "index.html")


def preview_upload(orchestrator):
    resume = request.files.get("resume")
    if not resume or not resume.filename:
        raise InvalidUpload("Upload your resume as a PDF.")

    target_role = request.form.get("target_role", "Data Scientist").strip()
    if target_role not in role_skill_requirements:
        raise InvalidUpload("Select a supported target role.")

    job_text = request.form.get("jd_text", "").strip()
    job_file = request.files.get("jd_file")
    resume_data = read_pdf_upload(resume, "Resume")
    if job_file and job_file.filename:
        job_data = read_pdf_upload(job_file, "Job description")
        if resume_data == job_data:
            raise InvalidUpload("Upload a different PDF for the job description.")
        try:
            with BytesIO(job_data) as job_stream:
                job_text = extract_text_from_pdf(job_stream, preserve_case=True)
        except UnreadablePDFError as error:
            raise InvalidUpload(f"Could not read the job description. {error}") from error

    if len(job_text) > MAX_JOB_TEXT:
        raise InvalidUpload("Job description must be 16,000 characters or fewer.")
    try:
        with BytesIO(resume_data) as resume_stream:
            return orchestrator.preview(resume_stream, job_text, target_role)
    except UnreadablePDFError as error:
        raise InvalidUpload(f"Resume upload failed. {error}") from error


@app.post("/preview")
def preview():
    state = preview_upload(Orchestrator())
    return jsonify(success=True, skill_catalog=skills, **{key: state[key] for key in PREVIEW_FIELDS})


@app.post("/analyze")
def analyze():
    review = parse_review(request.form.get("review"))
    orchestrator = Orchestrator()
    state = preview_upload(orchestrator)
    return result_response(orchestrator.analyze(state, review=review))


@app.post("/demo")
def demo():
    job_text = (EXAMPLES / "demo_job_description.txt").read_text(encoding="utf-8")
    state = Orchestrator().run(
        EXAMPLES / "demo_resume.pdf", job_text, "Data Analyst", include_ai=False
    )
    return result_response(state, demo=True)


@app.get("/health")
def health():
    return jsonify(status="CareerLaunch AI is running")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
