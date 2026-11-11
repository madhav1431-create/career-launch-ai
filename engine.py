import re

import pdfplumber

MAX_PDF_PAGES = 20


class UnreadablePDFError(ValueError):
    """A PDF could not be read as a text document."""


skills = [
    # Programming Languages
    "python", "java", "javascript", "typescript", "c++", "c#", "r", "scala", "go",
    
    # Web
    "react", "angular", "vue", "node.js", "html", "css", "flask", "fastapi", "django",
    
    # Data & ML
    "machine learning", "deep learning", "statistics", "numpy", "pandas",
    "scikit-learn", "tensorflow", "pytorch", "keras", "opencv", "nlp",
    "computer vision", "reinforcement learning", "transformers",
    
    # Data Engineering
    "sql", "mysql", "postgresql", "mongodb", "spark", "hadoop", "airflow",
    "kafka", "redis", "elasticsearch",
    
    # Cloud & DevOps
    "aws", "azure", "gcp", "docker", "kubernetes", "linux", "unix",
    "git", "github", "ci/cd", "terraform", "mlops",
    
    # General
    "data structures", "algorithms", "system design", "api", "rest api",
    "microservices", "agile", "excel", "power bi", "tableau"
]

_SKILL_ALIASES = {
    "javascript": ("js", "ecmascript"),
    "typescript": ("ts",),
    "c#": ("c sharp", "csharp"),
    "react": ("react.js", "reactjs"),
    "angular": ("angular.js", "angularjs"),
    "vue": ("vue.js", "vuejs"),
    "node.js": ("nodejs", "node js", "node-js"),
    "html": ("html5",),
    "css": ("css3",),
    "fastapi": ("fast api",),
    "machine learning": ("ml",),
    "deep learning": ("dl",),
    "numpy": ("num py",),
    "scikit-learn": ("scikit learn", "sklearn"),
    "tensorflow": ("tensor flow", "tf2"),
    "pytorch": ("py torch",),
    "nlp": ("natural language processing",),
    "postgresql": ("postgres",),
    "mongodb": ("mongo db", "mongo"),
    "spark": ("apache spark",),
    "airflow": ("apache airflow",),
    "kafka": ("apache kafka",),
    "aws": ("amazon web services",),
    "azure": ("microsoft azure",),
    "gcp": ("google cloud platform", "google cloud"),
    "kubernetes": ("k8s",),
    "ci/cd": ("ci / cd", "ci-cd", "ci cd", "cicd"),
    "mlops": ("ml ops", "ml-ops", "machine learning operations"),
    "api": ("apis",),
    "rest api": ("rest apis", "restful api", "restful apis", "rest-api", "rest-apis"),
    "power bi": ("powerbi",),
}

# Standalone R is case-sensitive. Go needs capitalization in a technical
# context or an unambiguous spelling because "go" is a common English verb.
_SPECIAL_SKILL_PATTERNS = {
    "r": r"(?i:r programming|r language)|R(?!&)",
    "go": r"(?i:golang|go programming|go language)|(?<=\bin )Go|Go(?=\s*[,;/|)\]]|$)",
    "c++": r"(?i:c)\+\+(?:98|03|11|14|17|20|23|26)?",
}


def _skill_expression(skill):
    if skill in _SPECIAL_SKILL_PATTERNS:
        return _SPECIAL_SKILL_PATTERNS[skill]
    spellings = (skill, *_SKILL_ALIASES.get(skill, ()))
    # A phrase may wrap once across two lines of an extracted PDF.
    space = r"(?:[^\S\n]+|[^\S\n]*\n[^\S\n]*)"
    terms = (
        space.join(map(re.escape, term.split()))
        for term in sorted(spellings, key=len, reverse=True)
    )
    return "(?i:" + "|".join(terms) + ")"


# Prefer longer terms when they overlap, such as "REST APIs" and "APIs".
_SKILL_GROUPS = {
    f"skill_{index}": skill
    for index, skill in enumerate(sorted(
        skills,
        key=lambda skill: max(map(len, (skill, *_SKILL_ALIASES.get(skill, ())))),
        reverse=True,
    ))
}
_SKILL_PATTERN = re.compile(
    r"(?<![\w+#])(?:"
    + "|".join(f"(?P<{group}>{_skill_expression(skill)})" for group, skill in _SKILL_GROUPS.items())
    + r")(?![\w+#])"
)

skill_graph = {
    "deep learning": ["machine learning"],
    "machine learning": ["python", "statistics"],
    "docker": ["linux"],
    "kubernetes": ["docker"],
    "pytorch": ["python", "deep learning"],
    "tensorflow": ["python", "deep learning"],
    "spark": ["python", "sql"],
    "nlp": ["python", "machine learning"],
    "computer vision": ["python", "deep learning", "opencv"],
    "fastapi": ["python"],
    "flask": ["python"],
}

# Standard skill requirements per role
role_skill_requirements = {
    "Data Scientist": [
        "python", "machine learning", "deep learning", "statistics",
        "pandas", "numpy", "scikit-learn", "sql", "tensorflow",
        "pytorch", "data structures", "git", "tableau"
    ],
    "ML Engineer": [
        "python", "machine learning", "deep learning", "pytorch",
        "tensorflow", "docker", "kubernetes", "aws", "git",
        "linux", "spark", "mlops", "fastapi", "sql"
    ],
    "Data Analyst": [
        "sql", "python", "excel", "tableau", "power bi",
        "statistics", "pandas", "numpy", "git", "postgresql"
    ],
    "Backend Developer": [
        "python", "java", "sql", "postgresql", "mongodb",
        "docker", "git", "linux", "rest api", "fastapi",
        "flask", "aws", "redis", "microservices"
    ],
    "AI Engineer": [
        "python", "machine learning", "deep learning", "pytorch",
        "tensorflow", "nlp", "computer vision", "docker",
        "aws", "git", "fastapi", "transformers", "kubernetes"
    ],
    "Frontend Developer": [
        "javascript", "typescript", "react", "html", "css",
        "git", "rest api", "node.js", "vue", "docker"
    ]
}

def get_role_skills(target_role):
    return role_skill_requirements.get(target_role, [
        "python", "sql", "git", "statistics", "machine learning"
    ])

def extract_text_from_pdf(file_path, *, preserve_case=False):
    """Extract text from a path or a seekable binary file."""
    try:
        with pdfplumber.open(file_path) as pdf:
            if len(pdf.pages) > MAX_PDF_PAGES:
                raise UnreadablePDFError(f"Upload a PDF with {MAX_PDF_PAGES} pages or fewer.")
            text = "\n\n".join(page.extract_text() or "" for page in pdf.pages)
    except UnreadablePDFError:
        raise
    except Exception as error:
        raise UnreadablePDFError("The PDF could not be read. Try a readable, unlocked PDF.") from error

    if not text.strip():
        raise UnreadablePDFError("No text could be extracted. Upload a text-based PDF.")
    return text if preserve_case else text.lower()


def detect_skills(text):
    return list(detect_skill_evidence(text))


def detect_skill_evidence(text):
    """Return the first original line supporting each recognized skill."""
    text = "\n".join(text.splitlines())
    evidence = {}
    for match in _SKILL_PATTERN.finditer(text):
        skill = _SKILL_GROUPS[match.lastgroup]
        if skill not in evidence:
            line_start = text.rfind("\n", 0, match.start()) + 1
            line_end = text.find("\n", match.end())
            if line_end == -1:
                line_end = len(text)
            evidence[skill] = text[line_start:line_end].strip()
    return {skill: evidence[skill] for skill in skills if skill in evidence}


def compute_skill_gap(resume_skills, jd_skills):

    gap = []

    for skill in jd_skills:
        if skill not in resume_skills:
            gap.append(skill)

    return gap


# ⭐ NEW FUNCTION
def generate_overview(role_hint, resume_skills, jd_skills, gap):

    strong = list(set(resume_skills).intersection(jd_skills))
    missing = gap

    if role_hint.strip() == "":
        role_hint = "this role"

    if len(strong) == 0:
        strength_line = "Your resume currently shows limited alignment with the job requirements."
    else:
        strength_line = (
            f"You already possess key skills such as {', '.join(strong[:6])} "
            "which align well with the job requirements."
        )

    if len(missing) == 0:
        gap_line = "There are no major skill gaps detected for this role."
    else:
        gap_line = (
            f"However, there are important gaps including {', '.join(missing[:5])}. "
            "Bridging these gaps will significantly improve your chances of being job-ready."
        )

    summary = (
        f"Based on your resume and the provided job description, you appear to be "
        f"a suitable candidate for the {role_hint} role. "
        f"{strength_line} {gap_line} "
        "Overall, your profile shows solid potential with clear areas for improvement."
    )

    # simple level inference
    if len(resume_skills) > 8:
        level = "Senior"
    elif len(resume_skills) > 4:
        level = "Mid"
    else:
        level = "Beginner"

    return summary, level
