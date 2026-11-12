"""Compare whole-term keywords with context-aware analysis on held-out synthetic PDFs."""

import argparse
import json
from collections import Counter
from contextlib import redirect_stdout
from io import BytesIO, StringIO
from pathlib import Path
from statistics import mean

import pymupdf

from core.orchestrator import Orchestrator
from engine import detect_skill_evidence
from training.benchmark import extraction_metrics, keyword_coverage, ranking_metrics


CASES_PATH = Path(__file__).with_name("benchmark_context_cases.json")
LAYOUTS = ("Single-column", "Two-column", "Two-page")


def resume_layout(pages):
    if len(pages) > 1:
        return "Two-page"
    if pages[0].get("sidebar"):
        return "Two-column"
    return "Single-column"


def make_resume_pdf(pages):
    """Lay out the fictional resumes in memory, then use the app's PDF reader."""
    with pymupdf.open() as pdf:
        for sections in pages:
            page = pdf.new_page(width=612, height=792)
            for column, x in (("main", 36), ("sidebar", 392)):
                for line_index, line in enumerate(sections.get(column, [])):
                    size = 14 if line_index == 0 else 10
                    page.insert_text((x, 64 + line_index * 20), line, fontsize=size)
        return BytesIO(pdf.tobytes())


def print_errors(label, expected, predicted):
    missing = ", ".join(sorted(expected - predicted)) or "none"
    extra = ", ".join(sorted(predicted - expected)) or "none"
    print(f"  {label}: missed {missing}; extra {extra}")


def evaluate(cases, details=False):
    comparisons = {
        "Resume evidence": [],
        "Required skills": [],
        "Preferred skills": [],
        "Explicit denials": [],
        **{layout: [] for layout in LAYOUTS},
    }
    layouts = Counter()
    rankings = []
    orchestrator = Orchestrator()

    for job in cases:
        description = job["description"]
        required = set(job["required"])
        preferred = set(job["preferred"])
        keyword_requirements = set(detect_skill_evidence(description, include_negated=True))
        candidates = []
        for resume in job["resumes"]:
            layout = resume_layout(resume["pages"])
            layouts[layout] += 1
            with make_resume_pdf(resume["pages"]) as pdf, redirect_stdout(StringIO()):
                result = orchestrator.run(pdf, description, job["role"], include_ai=False)

            if not candidates:
                current_required = set(result["required_skills"])
                current_preferred = set(result["preferred_skills"])
                comparisons["Required skills"].append((required, keyword_requirements, current_required))
                comparisons["Preferred skills"].append((preferred, set(), current_preferred))
                if details:
                    print(f"\n{job['id']}")
                    print_errors("Required", required, current_required)
                    print_errors("Preferred", preferred, current_preferred)

            expected_skills = set(resume["positive"])
            expected_denials = set(resume["negated"])
            keywords = set(detect_skill_evidence(result["resume_text"], include_negated=True))
            current_skills = set(result["resume_skills"])
            current_denials = set(result["negated_skill_evidence"])
            resume_comparison = (expected_skills, keywords, current_skills)
            comparisons["Resume evidence"].append(resume_comparison)
            comparisons[layout].append(resume_comparison)
            comparisons["Explicit denials"].append((expected_denials, set(), current_denials))

            scores = {
                "expected": keyword_coverage(expected_skills, required),
                "keywords": keyword_coverage(keywords, keyword_requirements),
                "context": result["match_score"] / 100,
            }
            candidates.append(scores)
            if details:
                print(f"\n  {resume['id']} ({layout})")
                print_errors("Resume evidence", expected_skills, current_skills)
                print_errors("Explicit denials", expected_denials, current_denials)
                print(
                    f"  Required coverage: expected {scores['expected']:.0%}, "
                    f"keywords {scores['keywords']:.0%}, context {scores['context']:.0%}"
                )
        rankings.append(candidates)
    return comparisons, rankings, layouts


def print_report(comparisons, rankings, layouts):
    print(f"\nHeld-out synthetic set: {sum(layouts.values())} resumes, {len(rankings)} job descriptions")
    print("PDF layouts: " + ", ".join(f"{layout.lower()} {layouts[layout]}" for layout in LAYOUTS))
    print("\nSkill evidence (micro-averaged precision, recall, and F1)")
    print(f"{'Measure':<18} {'Method':<14} {'Precision':>10} {'Recall':>8} {'F1':>8}")
    for name, cases in comparisons.items():
        for index, method in enumerate(("Keywords", "Context-aware"), start=1):
            precision, recall, f1 = extraction_metrics([(case[0], case[index]) for case in cases])
            print(f"{name:<18} {method:<14} {precision:>10.1%} {recall:>8.1%} {f1:>8.1%}")

    print("\nRequired skill coverage against hand labels")
    print(f"{'Method':<16} {'Coverage MAE':>14} {'Correct order':>15} {'Ties':>7}")
    for key, name in (("keywords", "Keywords"), ("context", "Context-aware")):
        error = mean(abs(candidate[key] - candidate["expected"]) for job in rankings for candidate in job)
        correct, ties, total = ranking_metrics(rankings, key)
        print(f"{name:<16} {error * 100:>11.1f} pp {f'{correct}/{total}':>15} {ties:>7}")
    print("\nBoth methods use the same skill vocabulary and PDF text.")
    print("The keyword baseline treats all job skill mentions as required and has no denial labels.")
    print("Coverage MAE is mean absolute error in percentage points.")
    print("Ordering compares resumes for the same job with different hand-labeled required coverage.")
    print("These examples measure evidence and coverage on synthetic documents.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--details", action="store_true", help="Show errors and coverage for each case.")
    args = parser.parse_args()
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    comparisons, rankings, layouts = evaluate(cases, args.details)
    print_report(comparisons, rankings, layouts)


if __name__ == "__main__":
    main()
