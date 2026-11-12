# CareerLaunch AI

[![Tests](https://github.com/madhav1431-create/career-launch-ai/actions/workflows/tests.yml/badge.svg)](https://github.com/madhav1431-create/career-launch-ai/actions/workflows/tests.yml) [MIT License](LICENSE)

CareerLaunch AI compares a resume with a target role, shows the evidence behind each skill match, and turns gaps into a learning plan and interview practice.

[**Try live demo**](https://madhav1431-create.github.io/career-launch-ai/) to explore a fictional Data Analyst report in your browser. Run the app locally to review your own resume.

![CareerLaunch AI dashboard showing skill coverage for the fictional Data Analyst demo](screenshots/dashboard.png)

## Try the dashboard

Install Python 3.11 or newer, then run these commands from a clone of this repository. A virtual environment is recommended.

```bash
python -m pip install -r requirements.txt
python api.py
```

Open [localhost:5000](http://127.0.0.1:5000) and select **Try demo** to analyze a [fictional resume](examples/demo_resume.pdf) against a [sample Data Analyst job](examples/demo_job_description.txt). The demo runs without credentials.

To analyze your own resume, upload a text-based PDF and select a target role. You can paste or upload a job description, or use the built-in role checklist. Select **Review detected skills** to confirm or correct your resume skills and the job's required and preferred skills before generating your report.

For optional Groq-generated coaching, copy `.env.example` to `.env` and set `GROQ_API_KEY`. The rule-based workflow also works when the provider is unavailable.

## How the dashboard works

- **Skill evidence.** The app detects whole skills and common aliases. Explicit denials such as “no experience with Python” appear separately from positive evidence. The review screen lets you correct what the app extracted.
- **Role coverage.** Required skills drive the main score. Preferred skills have a separate coverage figure. The built-in role checklists treat each skill as required.
- **Priority actions.** The overview shows up to three gaps with the requirement, resume evidence when available, and a practical step linked to the learning plan.
- **Practice hiring review.** ATS, recruiter, hiring manager, and technical panel views each show a concern, its supporting evidence, and a practical next step. [See the practice review](screenshots/hiring.png).
- **Learning and interview prep.** A prerequisite-aware roadmap orders the skill gaps. Project ideas and practice questions help turn the roadmap into work you can show.

The seven stages share request-local state. Resume evidence feeds role matching and gap analysis, then the learning planner, career strategist, interview coach, and practice hiring review. The dashboard includes the actual run log.

### Upload handling

PDFs are limited to 8 MB and 20 pages. The app processes each upload within its request and sends analysis responses with `Cache-Control: no-store`. With Groq enabled, the app sends the target role and structured skill context. The PDF and source lines stay in the application.

`python api.py` is for local development. To host the Flask app, serve `api:app` through a production WSGI server. The dashboard and API share an origin by default. Set `CAREERLAUNCH_ALLOWED_ORIGINS` to a comma-separated list only if you serve a separate frontend.

## PyTorch model experiment

The Streamlit demo uses a separate Siamese Transformer checkpoint for resume–job similarity and skill extraction. It has its own synthetic sample and displays similarity separately from skill coverage.

```bash
python -m pip install -r requirements-model.txt
python -m streamlit run app/model_streamlit_app.py
python -m training.benchmark --details
```

The [benchmark cases](training/benchmark_cases.json) contain 15 hand-labeled synthetic resumes and five job descriptions. The benchmark measures skill extraction precision, recall, and F1, plus how often each method orders candidates by the labeled skill coverage. Treat the results as a small diagnostic for this sample.

| Method | Precision | Recall | F1 | Correct candidate order |
| --- | ---: | ---: | ---: | ---: |
| Flask keyword matcher | 98.0% | 92.6% | 95.2% | 14/15 |
| Streamlit keyword baseline | 94.4% | 94.4% | 94.4% | 15/15 |
| Streamlit checkpoint + keywords | 22.4% | 94.4% | 36.2% | 14/15 |

The checkpoint added false positives and matched the Streamlit keyword baseline on recall for this sample. The model remains experimental.

## Held-out scoring benchmark

The [held-out cases](training/benchmark_context_cases.json) label 24 fictional resumes and eight job descriptions. The runner creates single-column, two-column, and two-page PDFs and reads them through the app. Both scoring methods use the same skill vocabulary and extracted text.

```bash
python -m pip install -r requirements.txt "PyMuPDF>=1.24,<2"
python -m training.benchmark_context --details
```

| Measure | Whole-term keywords | Context-aware scoring |
| --- | ---: | ---: |
| Positive resume evidence F1 | 84.5% | 94.0% |
| Required-skill classification F1 | 73.3% | 100.0% |
| Preferred-skill classification F1 | 0.0% | 96.8% |
| Mean absolute error in required coverage | 26.8 pp | 10.5 pp |
| Correct candidate order | 14/20 | 17/20 |

Context-aware scoring identified 68% of explicit denials in this sample. Two-page PDFs had the lowest positive-evidence F1 at 82.1%. Use these results to guide testing on more varied documents.

## Run tests

```bash
python -m unittest discover -s tests -v
```

Built by [Madhav Mittal](https://github.com/madhav1431-create) for the Microsoft Agents League Hackathon. Released under the [MIT License](LICENSE).
