from io import BytesIO
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.exceptions import RequestEntityTooLarge

from core.orchestrator import Orchestrator
from engine import UnreadablePDFError, extract_text_from_pdf, role_skill_requirements


load_dotenv()
ROOT = Path(__file__).resolve().parent
EXAMPLES = ROOT / "examples"
MAX_PDF_BYTES = 8 * 1024 * 1024
MAX_JOB_TEXT = 16_000
RESULT_FIELDS = (
    "target_role", "resume_skills", "jd_skills", "jd_source", "matched_skills",
    "skill_evidence", "requirement_evidence", "match_score", "overview",
    "missing_skills", "roadmap", "project_recommendations", "certifications",
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
    CORS(app, resources={r"/analyze": {"origins": allowed_origins}})


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
    return jsonify(success=True, demo=demo, **{key: state[key] for key in RESULT_FIELDS})


@app.after_request
def set_response_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    if request.endpoint in {"analyze", "demo"}:
        response.headers["Cache-Control"] = "no-store"
    return response


@app.errorhandler(RequestEntityTooLarge)
def request_too_large(_error):
    return jsonify(error="Upload is too large. Use PDFs of 8 MB or smaller."), 413


@app.get("/")
def index():
    return send_from_directory(ROOT, "index.html")


@app.post("/analyze")
def analyze():
    resume = request.files.get("resume")
    if not resume or not resume.filename:
        return jsonify(error="Upload your resume as a PDF."), 400

    target_role = request.form.get("target_role", "Data Scientist").strip()
    if target_role not in role_skill_requirements:
        return jsonify(error="Select a supported target role."), 400

    job_text = request.form.get("jd_text", "").strip()
    job_file = request.files.get("jd_file")

    try:
        resume_data = read_pdf_upload(resume, "Resume")
        if job_file and job_file.filename:
            job_data = read_pdf_upload(job_file, "Job description")
            if resume_data == job_data:
                raise InvalidUpload("Upload a different PDF for the job description.")
            try:
                with BytesIO(job_data) as job_stream:
                    job_text = extract_text_from_pdf(job_stream, preserve_case=True)
            except UnreadablePDFError as error:
                raise InvalidUpload(f"Job description: {error}") from error

        if len(job_text) > MAX_JOB_TEXT:
            raise InvalidUpload("Job description must be 16,000 characters or fewer.")
        with BytesIO(resume_data) as resume_stream:
            try:
                state = Orchestrator().run(resume_stream, job_text, target_role)
            except UnreadablePDFError as error:
                raise InvalidUpload(f"Resume: {error}") from error
    except InvalidUpload as error:
        return jsonify(error=str(error)), 400

    return result_response(state)


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
