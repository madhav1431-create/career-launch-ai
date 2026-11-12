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

_CLAUSE_BREAK = r"[;!?]|\.(?=\s|$)|\b(?:but|however|whereas|although|though)\b"
_CLAUSE_BOUNDARY = re.compile(_CLAUSE_BREAK, re.IGNORECASE)
_RESUME_CLAUSE_BOUNDARY = re.compile(r"\)|" + _CLAUSE_BREAK, re.IGNORECASE)
_NEGATION_PREFIX = re.compile(
    r"\b(?:"
    r"(?:no|without|lack(?:s|ing)?(?:\s+of)?)\s+(?:(?:any|prior|previous|professional|hands[- ]on|practical)\s+)*"
    r"(?:experience|exposure|knowledge|proficiency)(?:\s+(?:with|in|using|of))?"
    r"|(?:never|not(?:\s+yet)?|haven['’]t|hasn['’]t|hadn['’]t|don['’]t|doesn['’]t|didn['’]t)\s+"
    r"(?:used?|worked?\s+with|built\s+with|learned|learnt|know|touched|familiar\s+with)"
    r"|unfamiliar\s+with"
    r")\b",
    re.IGNORECASE,
)
_NEGATION_SUFFIX = re.compile(
    r"^\s*(?:[:(–—-]\s*|\bis\s+)?"
    r"(?:"
    r"no\s+(?:(?:prior|previous|professional|hands[- ]on|practical)\s+)*(?:experience|exposure|knowledge|proficiency)"
    r"|(?:experience|exposure)\s*:\s*none"
    r"|none|unfamiliar|never\s+used|not\s+(?:yet\s+)?(?:used|learned)"
    r")\b",
    re.IGNORECASE,
)
_LIST_GLUE = re.compile(r"(?:[\s,:/&()+|–—-]|\b(?:and|or|nor|either)\b)*", re.IGNORECASE)

_JD_HEADING = re.compile(
    r"^[^\S\n]*(?:[•*#-]+[^\S\n]*)?"
    r"(?:"
    r"(?P<preferred>preferred(?:\s+(?:skills|qualifications|requirements|experience))?"
    r"|nice[- ]to[- ]haves?(?:\s+(?:skills|qualifications))?|bonus(?:\s+(?:points|skills|qualifications))?"
    r"|desirable(?:\s+(?:skills|qualifications))?|optional(?:\s+(?:skills|qualifications))?|additional\s+qualifications)"
    r"|(?P<required>required(?:\s+(?:skills|qualifications|experience))?|requirements|qualifications"
    r"|minimum(?:\s+(?:qualifications|requirements))?|basic\s+qualifications"
    r"|must[- ]haves?|essential(?:\s+skills)?|what\s+you(?:['’]ll|\s+will)\s+need)"
    r"|(?P<other>responsibilities|about\s+(?:us|the\s+role)|benefits|what\s+you['’]ll\s+do)"
    r")[^\S\n]*(?:[:–—][^\S\n]*|$)",
    re.IGNORECASE | re.MULTILINE,
)
_JD_MARKER = re.compile(
    r"\b(?:"
    r"(?P<preferred>not\s+required|preferred|prefer(?:s)?|nice[- ]to[- ]have|desirable|optional"
    r"|bonus(?:\s+points)?|a\s+plus|an\s+advantage|ideally|helpful)"
    r"|(?P<required>required|must[- ]have|must\s+(?:know|use|demonstrate)|mandatory|essential|necessary)"
    r")\b",
    re.IGNORECASE,
)
_JD_PREFIX_GLUE = re.compile(
    r"(?:[\s,:/&()+|–—-]|\b(?:and|or|if|in|with|of|for|you|know|have|need|skills?|experience"
    r"|knowledge|familiarity|proficiency|hands[- ]on|working|prior|using|qualifications?"
    r"|includes?|including|such|as)\b)*",
    re.IGNORECASE,
)
_JD_SUFFIX_GLUE = re.compile(
    r"(?:[\s,:/&()+|–—-]|\b(?:and|or|experience|skills?|is|are|would|will|be|considered"
    r"|strongly|highly|a|an)\b)*",
    re.IGNORECASE,
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


def detect_skill_evidence(text, *, include_negated=False):
    """Return the first original line supporting each recognized skill."""
    if not include_negated:
        evidence, _ = classify_resume_skill_evidence(text)
        return evidence

    evidence = {}
    for skill, line, _, _, _ in _skill_mentions("\n".join(text.splitlines())):
        evidence.setdefault(skill, line)
    return _ordered_evidence(evidence)


def classify_resume_skill_evidence(text):
    """Return positive and explicitly negated skill evidence from resume text."""
    positive = {}
    negated = {}
    text = "\n".join(text.splitlines())
    for skill, line, before, after, position in _skill_mentions(text):
        if _is_negated(before, after):
            negated.setdefault(skill, line)
            continue

        previous_end = position - len(before) - 1
        if previous_end >= 0 and _LIST_GLUE.fullmatch(before):
            previous_start = text.rfind("\n", 0, previous_end) + 1
            previous = text[previous_start:previous_end].strip()
            continuation = (
                previous.lower().endswith((" with", " in", " using", " of", " or", " and", ","))
                or re.match(r"^\s*(?:and|or|nor)\b", before, re.IGNORECASE)
            )
            if continuation and _is_negated(f"{previous} {before}", after):
                negated.setdefault(skill, f"{previous}\n{line}")
                continue
        positive.setdefault(skill, line)
    return _ordered_evidence(positive), _ordered_evidence(negated)


def classify_requirement_evidence(text):
    """Return required and preferred evidence, giving required mentions precedence."""
    required = {}
    preferred = {}
    text = "\n".join(text.splitlines())
    headings = iter(_JD_HEADING.finditer(text))
    next_heading = next(headings, None)
    section = None
    for skill, line, before, after, position in _skill_mentions(text):
        while next_heading and next_heading.end() <= position:
            section = next_heading
            next_heading = next(headings, None)
        explicit_heading = section and section.end() > position - len(before)
        default = "preferred" if section and section.lastgroup == "preferred" else "required"
        priority = _inline_priority(before, after, default if explicit_heading else None)
        evidence = preferred if (priority or default) == "preferred" else required
        evidence.setdefault(skill, line)

    return _ordered_evidence(required), _ordered_evidence({
        skill: line for skill, line in preferred.items() if skill not in required
    })


def _skill_mentions(text):
    for match in _SKILL_PATTERN.finditer(text):
        start, end = match.span()
        line_start = text.rfind("\n", 0, start) + 1
        line_end = text.find("\n", end)
        if line_end == -1:
            line_end = len(text)
        yield (
            _SKILL_GROUPS[match.lastgroup],
            text[line_start:line_end].strip(),
            text[line_start:start],
            text[end:line_end],
            start,
        )


def _ordered_evidence(evidence):
    return {skill: evidence[skill] for skill in skills if skill in evidence}


def _is_negated(before, after):
    before = _RESUME_CLAUSE_BOUNDARY.split(before)[-1]
    after = _CLAUSE_BOUNDARY.split(after, maxsplit=1)[0]
    for marker in _NEGATION_PREFIX.finditer(before):
        if _LIST_GLUE.fullmatch(_SKILL_PATTERN.sub("", before[marker.end():])):
            return True
    if _NEGATION_SUFFIX.match(after):
        return True
    # A bare "no" or "zero" counts only when it directly qualifies the skill
    # or a list of skills, avoiding phrases such as "no SQL migration issues".
    for marker in re.finditer(r"\b(?:no|zero)\s+", before, re.IGNORECASE):
        if _LIST_GLUE.fullmatch(_SKILL_PATTERN.sub("", before[marker.end():])):
            tail = _SKILL_PATTERN.sub("", after)
            return bool(_LIST_GLUE.fullmatch(tail) or re.match(
                r"^(?:[\s,/:]|\b(?:and|or|nor)\b)*(?:experience|skills?|knowledge|proficiency|exposure|yet)\b",
                tail,
                re.IGNORECASE,
            ))
    return False


def _inline_priority(before, after, heading_priority):
    before = _CLAUSE_BOUNDARY.split(before)[-1]
    after = _CLAUSE_BOUNDARY.split(after, maxsplit=1)[0]
    prefix_priority = heading_priority
    for marker in _JD_MARKER.finditer(before):
        if _JD_PREFIX_GLUE.fullmatch(_SKILL_PATTERN.sub("", before[marker.end():])):
            prefix_priority = marker.lastgroup

    for marker in _JD_MARKER.finditer(after):
        between = after[:marker.start()]
        if not _JD_SUFFIX_GLUE.fullmatch(_SKILL_PATTERN.sub("", between)):
            break
        if prefix_priority and "," in between:
            break
        return marker.lastgroup
    return prefix_priority


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
