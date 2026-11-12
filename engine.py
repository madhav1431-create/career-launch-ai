import re
from collections import Counter

import pdfplumber
from pdfplumber.utils import cluster_objects

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
_RESUME_CLAUSE_BOUNDARY = re.compile(r"\)|\binstead\b|,\s*yet\b|" + _CLAUSE_BREAK, re.IGNORECASE)
_EXPERIENCE_MODIFIERS = (
    r"(?:(?:any|prior|previous|professional|production|commercial|paid|hands[- ]on|"
    r"practical|formal|direct|real[- ]world|working|project|work)\s+)*"
)
_EXPERIENCE_TERMS = r"(?:experience|exposure|knowledge|proficiency|familiarity|practice|work|use)"
_EXPERIENCE_LINK = (
    r"(?:\s+(?:with|in|of|on|to)(?:\s+using)?"
    r"|\s+(?:using|involving|(?:working|developing|building|deploying)\s+(?:with|in|on)))?"
)
_USE_VERBS = (
    r"(?:used?|using|work(?:ed)?\s+(?:with|in|on)|built(?:\s+with)?|build(?:\s+with)?"
    r"|written|wrote|write|developed(?:\s+with)?|deployed(?:\s+with)?"
    r"|learned|learnt|learn|know|touched|familiar\s+with)"
)
_NEGATION_WORDS = r"(?:no|zero|without|lack(?:s|ing)?(?:\s+of)?)"
_NEGATION_PREFIX = re.compile(
    r"\b(?:"
    + _NEGATION_WORDS + r"\s+" + _EXPERIENCE_MODIFIERS + _EXPERIENCE_TERMS
    + _EXPERIENCE_LINK
    + r"|(?:never|not|haven['’]t|hasn['’]t|hadn['’]t|don['’]t|doesn['’]t|didn['’]t|yet\s+to)\s+"
    + r"(?:yet\s+)?(?:had\s+(?:a|the)\s+(?:chance|opportunity)\s+to\s+)?"
    + _USE_VERBS
    + r"|(?:unfamiliar\s+with|without\s+using)"
    r")\b",
    re.IGNORECASE,
)
_NEGATION_SUFFIX = re.compile(
    r"(?P<aside>\()?\s*(?:[:–—-]\s*|\bis\s+)?"
    r"(?:"
    + _NEGATION_WORDS + r"\s+" + _EXPERIENCE_MODIFIERS + _EXPERIENCE_TERMS
    + r"|" + _EXPERIENCE_TERMS + r"\s*:\s*none"
    + r"|none|unfamiliar|never\s+used|not\s+(?:yet\s+)?(?:used|learned)"
    r")\b",
    re.IGNORECASE,
)
_BARE_NEGATION = re.compile(r"\b(?:no|zero)\s+" + _EXPERIENCE_MODIFIERS, re.IGNORECASE)
_LIST_GLUE = re.compile(r"(?:[\s,:/&()+|–—•*▪◦‣-]|\b(?:and|or|nor|either)\b)*", re.IGNORECASE)
_LIST_SEPARATOR = re.compile(r"[,/&|•]|\b(?:and|or|nor)\b", re.IGNORECASE)
_BULLET = re.compile(r"^(?:[-•*▪◦‣–—]|\d+[.)])\s+")
_RESUME_HEADING = re.compile(
    r"^(?:skills|technical\s+skills|toolbox|tools|experience|work\s+experience|professional\s+experience"
    r"|projects|personal\s+projects|education|summary|profile|certifications|employment)\s*:?\s*$",
    re.IGNORECASE,
)
_WRAPPED_BEFORE = re.compile(
    r"(?:,|\b(?:and|or|nor|with|without|in|using|involving|of|on|to|no|zero|never|not|yet|hands[- ]on)"
    r"|(?:haven|hasn|hadn|don|doesn|didn)['’]t)$",
    re.IGNORECASE,
)
_WRAPPED_AFTER = re.compile(r"^(?:and|or|nor|with|in|using|of|but|although|however)\b", re.IGNORECASE)

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
            text = "\n\n".join(_read_pdf_page(page) for page in pdf.pages)
    except UnreadablePDFError:
        raise
    except Exception as error:
        raise UnreadablePDFError("The PDF could not be read. Try a readable, unlocked PDF.") from error

    if not text.strip():
        raise UnreadablePDFError("No text could be extracted. Upload a text-based PDF.")
    return text if preserve_case else text.lower()


def _read_pdf_page(page):
    rows = [
        sorted(row, key=lambda word: word["x0"])
        for row in cluster_objects(page.extract_words(), "top", tolerance=3)
    ]
    gutter = max(16, page.width * 0.028)
    left_edge = page.bbox[0] + page.width * 0.19
    right_edge = page.bbox[0] + page.width * 0.89
    anchors = Counter()
    for row in rows:
        for index, word in enumerate(row):
            start = word["x0"]
            if left_edge < start < right_edge and (not index or start - row[index - 1]["x1"] >= gutter):
                anchors[round(start / 4) * 4] += 1

    best_score, best_text = 0, ""
    # Testing only recurring anchors bounds the work even for very wide pages.
    for anchor, occurrences in anchors.most_common(16):
        if occurrences < 2:
            break
        score, text = _read_column_regions(rows, anchor - gutter / 2, gutter)
        if score > best_score:
            best_score, best_text = score, text
    return best_text if best_score else page.extract_text() or ""


def _read_column_regions(rows, split, gutter):
    """Keep spanning rows in order and read each parallel region by column."""
    score = 0
    sections = []
    region = []
    for row in rows:
        left = [word for word in row if word["x1"] <= split]
        right = [word for word in row if word["x0"] >= split]
        spans_gutter = len(left) + len(right) != len(row) or (
            left and right and right[0]["x0"] - left[-1]["x1"] < gutter
        )
        if spans_gutter:
            region_score, region_text = _read_column_region(region)
            score += region_score
            if region_text:
                sections.append(region_text)
            sections.append(_join_words(row))
            region = []
        else:
            region.append((row, left, right))
    region_score, region_text = _read_column_region(region)
    if region_text:
        sections.append(region_text)
    return score + region_score, "\n\n".join(sections)


_DATE_WORDS = re.compile(
    r"\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?"
    r"|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?|present|current)\b",
    re.IGNORECASE,
)


def _read_column_region(region):
    left_lines = [left for _, left, _ in region if left]
    right_lines = [right for _, _, right in region if right]
    # A date or year aligned on the right is common in a single-column resume.
    left_body = [line for line in left_lines if _has_body_words(line)]
    right_body = [line for line in right_lines if _has_body_words(line)]
    if len(left_body) >= 2 and len(right_body) >= 2:
        first_shared_row = max(left_body[0][0]["top"], right_body[0][0]["top"])
        last_shared_row = min(left_body[-1][0]["top"], right_body[-1][0]["top"])
        if first_shared_row < last_shared_row:
            return min(len(left_body), len(right_body)), "\n\n".join(
                "\n".join(_join_words(line) for line in column)
                for column in (left_lines, right_lines)
            )
    return 0, "\n".join(_join_words(row) for row, _, _ in region)


def _has_body_words(line):
    return bool(re.search(r"[a-z]{2,}", _DATE_WORDS.sub("", _join_words(line)), re.IGNORECASE))


def _join_words(words):
    return " ".join(word["text"] for word in words)


def detect_skills(text):
    return list(detect_skill_evidence(text))


def detect_skill_evidence(text, *, include_negated=False):
    """Return the first original line supporting each recognized skill."""
    if not include_negated:
        evidence, _ = classify_resume_skill_evidence(text)
        return evidence

    evidence = {}
    text = "\n".join(text.splitlines())
    for skill, _, _, line_start, line_end in _skill_mentions(text):
        evidence.setdefault(skill, text[line_start:line_end].strip())
    return _ordered_evidence(evidence)


def classify_resume_skill_evidence(text):
    """Return positive and explicitly negated skill evidence from resume text."""
    positive = {}
    negated = {}
    text = "\n".join(text.splitlines())
    regions = iter(_resume_context_regions(text))
    region_start, region_end = next(regions)
    for skill, start, end, line_start, line_end in _skill_mentions(text):
        while start >= region_end:
            region_start, region_end = next(regions)
        bounds = _negation_bounds(text[region_start:start], text[end:max(region_end, line_end)])
        if bounds is None:
            positive.setdefault(skill, text[line_start:line_end].strip())
        else:
            before, after = bounds
            excerpt_start = text.rfind("\n", 0, start + before) + 1
            excerpt_end = text.find("\n", end + after)
            excerpt = text[excerpt_start:excerpt_end if excerpt_end >= 0 else len(text)].strip()
            negated.setdefault(skill, "\n".join(line.strip() for line in excerpt.splitlines()))
    return _ordered_evidence(positive), _ordered_evidence(negated)


def _resume_context_regions(text):
    """Join wrapped clauses and explicit denial lists without crossing layout boundaries."""
    region_start = position = 0
    previous = ""
    denial_list = False
    for physical_line in text.splitlines(keepends=True):
        line = physical_line.strip()
        continuation = bool(previous and line and (
            (denial_list and _is_skill_list(line))
            or (
                not _BULLET.match(line) and not _RESUME_HEADING.fullmatch(line)
                and (_WRAPPED_BEFORE.search(previous) or _WRAPPED_AFTER.match(line))
            )
        ))
        if position and not continuation:
            yield region_start, position
            region_start = position
        if not continuation:
            denial_list = line.endswith(":") and bool(_NEGATION_PREFIX.search(line))
        previous = line
        position += len(physical_line)
    yield region_start, len(text)


def classify_requirement_evidence(text):
    """Return required and preferred evidence, giving required mentions precedence."""
    required = {}
    preferred = {}
    text = "\n".join(text.splitlines())
    headings = iter(_JD_HEADING.finditer(text))
    next_heading = next(headings, None)
    section = None
    for skill, start, end, line_start, line_end in _skill_mentions(text):
        while next_heading and next_heading.end() <= start:
            section = next_heading
            next_heading = next(headings, None)
        explicit_heading = section and section.end() > line_start
        default = "preferred" if section and section.lastgroup == "preferred" else "required"
        priority = _inline_priority(text[line_start:start], text[end:line_end], default if explicit_heading else None)
        evidence = preferred if (priority or default) == "preferred" else required
        evidence.setdefault(skill, text[line_start:line_end].strip())

    return _ordered_evidence(required), _ordered_evidence({
        skill: line for skill, line in preferred.items() if skill not in required
    })


def _skill_mentions(text):
    for match in _SKILL_PATTERN.finditer(text):
        start, end = match.span()
        line_start = text.rfind("\n", 0, start) + 1
        line_end = text.find("\n", end)
        yield _SKILL_GROUPS[match.lastgroup], start, end, line_start, line_end if line_end >= 0 else len(text)


def _ordered_evidence(evidence):
    return {skill: evidence[skill] for skill in skills if skill in evidence}


def _negation_bounds(before, after):
    before = _RESUME_CLAUSE_BOUNDARY.split(before)[-1]
    after = _CLAUSE_BOUNDARY.split(after, maxsplit=1)[0]
    for marker in _NEGATION_PREFIX.finditer(before):
        if _is_skill_list(before[marker.end():]):
            return marker.start() - len(before), 0
    for marker in _NEGATION_SUFFIX.finditer(after):
        between = after[:marker.start()]
        if marker.group("aside") and not _LIST_GLUE.fullmatch(between):
            continue
        if _is_skill_list(between):
            return 0, marker.end()
    # A bare "no" or "zero" counts only when it directly qualifies the skill
    # or a list of skills, avoiding phrases such as "no SQL migration issues".
    for marker in _BARE_NEGATION.finditer(before):
        if not _is_skill_list(before[marker.end():]):
            continue
        if _is_skill_list(after):
            return marker.start() - len(before), 0
        for term in re.finditer(r"\b(?:" + _EXPERIENCE_TERMS + r"|skills?|yet)\b", after, re.IGNORECASE):
            if _is_skill_list(after[:term.start()]):
                return marker.start() - len(before), term.end()
    return None


def _is_skill_list(text):
    if _LIST_GLUE.fullmatch(_SKILL_PATTERN.sub("", text)):
        return True
    # A term outside the catalog may occur between two separators in a list.
    # Require a complete, recognizable identifier shape in that position.
    items = _LIST_SEPARATOR.split(text)
    for index, item in enumerate(items):
        if _LIST_GLUE.fullmatch(_SKILL_PATTERN.sub("", item)):
            continue
        name = item.strip(" \t\n():–—-")
        if index == len(items) - 1 or not re.fullmatch(r"\.?[A-Z0-9][A-Za-z0-9.+#-]{1,30}", name):
            return False
    return True


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
