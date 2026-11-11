"""Evaluate the Flask matcher and the Streamlit checkpoint on synthetic text pairs."""

import argparse
import json
from contextlib import redirect_stdout
from io import StringIO
from itertools import combinations
from pathlib import Path

import torch

from agents.match_agent import MatchAgent
from data.dataset import extract_skills
from engine import detect_skills
from training.inference import OnboardingEngine
from utils.text_utils import normalize_for_model


ROOT = Path(__file__).resolve().parent.parent
CASES_PATH = Path(__file__).with_name("benchmark_cases.json")
SPELLINGS = {"cicd": "ci/cd", "nodejs": "node.js"}


def canonical_skills(skills):
    return {SPELLINGS.get(skill, skill) for skill in skills}


def coverage(resume_skills, job_skills):
    return len(resume_skills & job_skills) / len(job_skills) if job_skills else 0.0


def flask_coverage(resume_skills, job_skills):
    state = {"resume_skills": resume_skills, "jd_skills": job_skills, "agent_logs": []}
    with redirect_stdout(StringIO()):
        MatchAgent().run(state)
    return state["match_score"] / 100


def extraction_metrics(predictions):
    correct = sum(len(expected & predicted) for expected, predicted in predictions)
    predicted_count = sum(len(predicted) for _, predicted in predictions)
    expected_count = sum(len(expected) for expected, _ in predictions)
    precision = correct / predicted_count if predicted_count else 0.0
    recall = correct / expected_count if expected_count else 0.0
    all_labels = predicted_count + expected_count
    f1 = 2 * correct / all_labels if all_labels else 0.0
    return precision, recall, f1


def ranking_metrics(jobs, score_name):
    correct = ties = total = 0
    for candidates in jobs:
        for first, second in combinations(candidates, 2):
            expected = first["expected"] - second["expected"]
            if expected == 0:
                continue
            difference = first[score_name] - second[score_name]
            if difference == 0:
                ties += 1
            elif difference * expected > 0:
                correct += 1
            total += 1
    return correct, ties, total


def evaluate(model, cases, details):
    extraction = {"Flask keywords": [], "Model demo keywords": [], "Checkpoint + keywords": []}
    jobs = []
    for job in cases:
        description = job["description"]
        expected_job = canonical_skills(job["skills"])
        flask_job = canonical_skills(detect_skills(description))
        demo_job = canonical_skills(extract_skills(normalize_for_model(description)))
        candidates = []
        for resume in job["resumes"]:
            text = resume["text"]
            expected_resume = canonical_skills(resume["skills"])
            flask_resume = canonical_skills(detect_skills(text))
            demo_resume = canonical_skills(extract_skills(normalize_for_model(text)))
            result = model.analyze(resume_text=text, jd_text=description)
            if result["method"] != "model":
                raise RuntimeError(f"Checkpoint inference failed on {job['id']}/{resume['id']}.")
            model_resume = canonical_skills(result["resume_skills"])
            model_job = canonical_skills(result["jd_skills"])

            if not candidates:
                extraction["Flask keywords"].append((expected_job, flask_job))
                extraction["Model demo keywords"].append((expected_job, demo_job))
                extraction["Checkpoint + keywords"].append((expected_job, model_job))
            extraction["Flask keywords"].append((expected_resume, flask_resume))
            extraction["Model demo keywords"].append((expected_resume, demo_resume))
            extraction["Checkpoint + keywords"].append((expected_resume, model_resume))

            scores = {
                "expected": coverage(expected_resume, expected_job),
                "flask": flask_coverage(flask_resume, flask_job),
                "demo": coverage(demo_resume, demo_job),
                "checkpoint": result["match_score"],
            }
            candidates.append(scores)
            if details:
                print(f"\n{job['id']}/{resume['id']}")
                print(f"  Gold resume skills: {', '.join(sorted(expected_resume)) or '(none)'}")
                for name, predicted in (
                    ("Flask keywords", flask_resume),
                    ("Model demo keywords", demo_resume),
                    ("Checkpoint + keywords", model_resume),
                ):
                    extra = ", ".join(sorted(predicted - expected_resume)) or "(none)"
                    missed = ", ".join(sorted(expected_resume - predicted)) or "(none)"
                    print(f"  {name}: extra {extra}; missed {missed}")
                print(
                    f"  Gold coverage {scores['expected']:.2f}; Flask {scores['flask']:.2f}; "
                    f"demo keywords {scores['demo']:.2f}; checkpoint similarity {scores['checkpoint']:.3f}"
                )
        jobs.append(candidates)
    return extraction, jobs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--details", action="store_true", help="Show each resume's errors and scores.")
    args = parser.parse_args()
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    torch.set_num_threads(1)
    model = OnboardingEngine(checkpoint=ROOT / "checkpoints" / "best_model.pt", device="cpu")
    if not model.has_model:
        parser.error("The repository checkpoint and its tokenizer are required.")

    extraction, jobs = evaluate(model, cases, args.details)
    resume_count = sum(len(candidates) for candidates in jobs)
    print(f"\nHand-labeled synthetic set: {resume_count} resumes, {len(jobs)} job descriptions")
    print("\nSkill extraction (micro-averaged across resumes and unique job descriptions)")
    print(f"{'Method':<24} {'Precision':>10} {'Recall':>8} {'F1':>8}")
    for name, predictions in extraction.items():
        precision, recall, f1 = extraction_metrics(predictions)
        print(f"{name:<24} {precision:>10.1%} {recall:>8.1%} {f1:>8.1%}")

    print("\nRanking against hand-labeled skill coverage (same job, unequal expected coverage)")
    print(f"{'Method':<27} {'Correct':>10} {'Ties':>8}")
    for score_name, name in (
        ("flask", "Flask skill coverage"),
        ("demo", "Demo keyword coverage"),
        ("checkpoint", "Checkpoint similarity"),
    ):
        correct, ties, total = ranking_metrics(jobs, score_name)
        print(f"{name:<27} {f'{correct}/{total}':>10} {ties:>8}")
    print("\nThese short fictional examples measure skill evidence and ordering, not hiring outcomes.")


if __name__ == "__main__":
    main()
