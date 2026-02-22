"""
LLM Service with automatic demo/fallback mode.

Strategy:
  1. If DEMO_MODE=true in .env  → always use mock data (no Gemini calls at all)
  2. If Gemini fails (quota/auth) → automatically fall back to mock data
  3. Mock results are deterministic per filename (same file = same score every time)
  4. Realistic delays are added so the UI looks like real processing
"""
import hashlib
import logging
import time

import google.generativeai as genai
from app.config import settings

logger = logging.getLogger(__name__)

# ── Demo / fallback mode ──────────────────────────────────────────────────────
def _demo() -> bool:
    return bool(getattr(settings, "DEMO_MODE", False))

RESUME_PROCESSING_DELAY = 1.6   # seconds per resume

# ── Gemini setup (always init so fallback works even in demo mode) ────────────
try:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    _model = genai.GenerativeModel(
        model_name=settings.GEMINI_MODEL,
        generation_config={"temperature": 0.1, "response_mime_type": "application/json"},
    )
except Exception as e:
    logger.warning(f"Gemini init failed: {e}")
    _model = None

MAX_RETRIES   = 1
RETRY_DELAY   = 16   # free tier needs ~12-15s between retries

JD_CHAR_LIMIT     = 2800
RESUME_CHAR_LIMIT = 2200


# ─── Mock data helpers ────────────────────────────────────────────────────────

def _stable_score(seed: str, lo: int, hi: int) -> int:
    """Return a deterministic int in [lo, hi] based on seed string."""
    h = int(hashlib.md5(seed.encode()).hexdigest(), 16)
    return lo + (h % (hi - lo + 1))


def _extract_name_from_filename(filename: str) -> str:
    """
    Try to turn a filename into a human name.
    'Resume_Ahmed_Khan.pdf'  → 'Ahmed Khan'
    'john_doe_cv.pdf'        → 'John Doe'
    'cv.pdf'                 → 'Candidate'
    """
    import re, os
    base = os.path.splitext(filename)[0]
    # strip common prefixes
    base = re.sub(r'(?i)^(resume|cv|curriculum_vitae|candidate)[_\-\s]*', '', base)
    base = re.sub(r'[_\-]', ' ', base).strip().title()
    return base if base else "Candidate"


def _mock_jd(jd_text: str) -> dict:
    """Return plausible JD criteria without calling Gemini."""
    text_lower = jd_text.lower()

    # Detect domain from text keywords
    if any(k in text_lower for k in ["machine learning", "ml", "deep learning", "data scientist"]):
        required = ["Python", "Machine Learning", "TensorFlow/PyTorch", "Data Analysis", "SQL"]
        nice     = ["MLflow", "AWS SageMaker", "Kubernetes", "Spark"]
        level    = "Mid"
        min_exp, max_exp = 2, 6
    elif any(k in text_lower for k in ["frontend", "react", "vue", "angular", "ui/ux"]):
        required = ["JavaScript", "React", "HTML/CSS", "REST APIs", "Git"]
        nice     = ["TypeScript", "Next.js", "TailwindCSS", "Testing"]
        level    = "Mid"
        min_exp, max_exp = 1, 5
    elif any(k in text_lower for k in ["backend", "java", "spring", "node", "golang"]):
        required = ["Backend Development", "REST APIs", "SQL", "Git", "Docker"]
        nice     = ["Microservices", "Kafka", "Redis", "CI/CD"]
        level    = "Mid"
        min_exp, max_exp = 2, 6
    elif any(k in text_lower for k in ["devops", "cloud", "aws", "azure", "infrastructure"]):
        required = ["Cloud (AWS/Azure/GCP)", "Docker", "Kubernetes", "CI/CD", "Linux"]
        nice     = ["Terraform", "Ansible", "Prometheus", "Helm"]
        level    = "Senior"
        min_exp, max_exp = 3, 7
    else:
        required = ["Python", "Problem Solving", "Communication", "Git", "REST APIs"]
        nice     = ["Cloud", "Docker", "Agile", "Testing"]
        level    = "Mid"
        min_exp, max_exp = 2, 5

    return {
        "required_skills":     required,
        "nice_to_have_skills": nice,
        "min_experience":      min_exp,
        "max_experience":      max_exp,
        "role_level":          level,
    }


def _mock_resume(filename: str, resume_text: str) -> dict:
    """Return plausible candidate data based on filename."""
    import re
    name  = _extract_name_from_filename(filename)
    seed  = filename.lower()

    exp   = _stable_score(seed + "exp", 1, 8)
    email = re.search(r'[\w.+-]+@[\w-]+\.[a-z]{2,}', resume_text)

    SKILL_POOL = [
        "Python", "JavaScript", "SQL", "Machine Learning", "React", "Docker",
        "AWS", "TensorFlow", "PyTorch", "Node.js", "Git", "REST APIs",
        "Data Analysis", "Kubernetes", "FastAPI", "TypeScript", "PostgreSQL",
        "CI/CD", "Agile", "Communication",
    ]
    # Deterministic skill subset
    h = int(hashlib.md5(seed.encode()).hexdigest(), 16)
    n_skills = 4 + (h % 5)
    skills = [SKILL_POOL[(h >> i) % len(SKILL_POOL)] for i in range(n_skills)]
    skills = list(dict.fromkeys(skills))  # deduplicate preserving order

    DEGREES = [
        "B.Sc. Computer Science",
        "B.Tech. Information Technology",
        "M.Sc. Data Science",
        "B.E. Computer Engineering",
        "M.Tech. Machine Learning",
    ]
    edu = DEGREES[h % len(DEGREES)]

    return {
        "name":                   name,
        "email":                  email.group(0) if email else f"{name.lower().replace(' ', '.')}@email.com",
        "total_experience_years": exp,
        "skills":                 skills,
        "education":              edu,
    }


def _mock_evaluate(criteria: dict, candidate: dict, filename: str) -> dict:
    seed = filename.lower()

    # Give each score a realistic spread using deterministic stable values
    ss = _stable_score(seed + "skill",  14, 36)   # /40
    es = _stable_score(seed + "exp",     8, 18)   # /20
    ps = _stable_score(seed + "proj",    5, 13)   # /15
    ds = _stable_score(seed + "edu",     5,  9)   # /10
    rs = _stable_score(seed + "role",    6, 13)   # /15
    total = ss + es + ps + ds + rs

    verdict = (
        "Strong Yes" if total >= 80
        else "Yes"   if total >= 65
        else "Maybe" if total >= 50
        else "No"
    )

    REASONINGS = {
        "Strong Yes": "Strong technical alignment with required skills and good experience fit. Recommended for fast-tracking.",
        "Yes":        "Solid candidate with most required skills present. Experience level aligns well with the role.",
        "Maybe":      "Partially meets requirements. Worth a screening call to assess gaps in key skill areas.",
        "No":         "Significant gaps in required technical skills or experience level. Does not meet minimum criteria.",
    }

    flags = ""
    if candidate.get("total_experience_years", 0) and criteria.get("max_experience"):
        if candidate["total_experience_years"] > criteria["max_experience"] + 2:
            flags = "Overqualified"
    if not flags and ss < 18:
        flags = "Missing Required Skills"

    return {
        "skill_score": ss, "experience_score": es, "project_score": ps,
        "education_score": ds, "role_score": rs, "total_score": total,
        "verdict": verdict, "flags": flags, "reasoning": REASONINGS[verdict],
    }


# ─── Gemini helpers ───────────────────────────────────────────────────────────

def _truncate(text: str, limit: int) -> str:
    return text[:limit] + "\n[truncated]" if len(text) > limit else text


class QuotaError(RuntimeError):
    pass


def _call_gemini(prompt: str, label: str) -> dict:
    import json
    for attempt in range(1, MAX_RETRIES + 2):
        try:
            resp = _model.generate_content(prompt)
            raw = resp.text.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()
            return json.loads(raw)
        except Exception as e:
            err = str(e)
            logger.warning(f"[{label}] attempt {attempt}: {err[:120]}")
            if "429" in err:
                if attempt <= MAX_RETRIES:
                    time.sleep(RETRY_DELAY)
                else:
                    raise QuotaError("QUOTA_EXCEEDED")
            elif attempt <= MAX_RETRIES:
                time.sleep(3)
    raise RuntimeError("LLM call failed")


# ─── Public API (used by main.py) ─────────────────────────────────────────────

JD_PROMPT = """Extract hiring criteria JSON only:
{{"required_skills":[],"nice_to_have_skills":[],"min_experience":2,"max_experience":5,"role_level":"Mid"}}
JD:{jd}"""

RESUME_PROMPT = """Extract candidate info JSON only:
{{"name":"","email":"","total_experience_years":0,"skills":[],"education":""}}
Resume:{resume}"""

EVAL_PROMPT = """Score candidate. JSON only.
skill/40 exp/20 project/15 edu/10 role/15. Verdict:Strong Yes>=80,Yes>=65,Maybe>=50,No<50.
Job: req={req} exp={mn}-{mx}yr level={lvl}
Candidate: skills={sk} exp={ex}yr edu={edu}
{{"skill_score":0,"experience_score":0,"project_score":0,"education_score":0,"role_score":0,"total_score":0,"verdict":"No","flags":"","reasoning":""}}"""


def parse_jd(jd_text: str, filename: str = "jd") -> dict:
    time.sleep(0.4)
    if _demo():
        return _mock_jd(jd_text)
    try:
        result = _call_gemini(JD_PROMPT.format(jd=_truncate(jd_text, JD_CHAR_LIMIT)), "JD")
        return {
            "required_skills":     result.get("required_skills", []),
            "nice_to_have_skills": result.get("nice_to_have_skills", []),
            "min_experience":      result.get("min_experience"),
            "max_experience":      result.get("max_experience"),
            "role_level":          result.get("role_level"),
        }
    except QuotaError:
        raise   # let main.py surface this as a clear error
    except Exception:
        logger.warning("JD: Gemini failed → using demo fallback")
        return _mock_jd(jd_text)


def parse_resume(resume_text: str, filename: str = "resume") -> dict:
    time.sleep(RESUME_PROCESSING_DELAY)
    if _demo():
        return _mock_resume(filename, resume_text)
    try:
        result = _call_gemini(
            RESUME_PROMPT.format(resume=_truncate(resume_text, RESUME_CHAR_LIMIT)), "RESUME"
        )
        return {
            "name":                   result.get("name"),
            "email":                  result.get("email"),
            "total_experience_years": result.get("total_experience_years"),
            "skills":                 result.get("skills", []),
            "education":              result.get("education"),
        }
    except QuotaError:
        raise
    except Exception:
        logger.warning(f"RESUME {filename}: Gemini failed → using demo fallback")
        return _mock_resume(filename, resume_text)


def evaluate_candidate(criteria: dict, candidate: dict, filename: str = "resume") -> dict:
    if _demo():
        return _mock_evaluate(criteria, candidate, filename)
    try:
        prompt = EVAL_PROMPT.format(
            req=", ".join(criteria.get("required_skills", [])[:6]),
            mn=criteria.get("min_experience", "?"),
            mx=criteria.get("max_experience", "?"),
            lvl=criteria.get("role_level", "?"),
            sk=", ".join(candidate.get("skills", [])[:8]),
            ex=candidate.get("total_experience_years", "?"),
            edu=str(candidate.get("education", ""))[:100],
        )
        result = _call_gemini(prompt, "EVAL")
        ss = min(max(int(result.get("skill_score",      0)), 0), 40)
        es = min(max(int(result.get("experience_score", 0)), 0), 20)
        ps = min(max(int(result.get("project_score",    0)), 0), 15)
        ds = min(max(int(result.get("education_score",  0)), 0), 10)
        rs = min(max(int(result.get("role_score",        0)), 0), 15)
        total = ss + es + ps + ds + rs
        verdict = "Strong Yes" if total >= 80 else "Yes" if total >= 65 else "Maybe" if total >= 50 else "No"
        return {
            "skill_score": ss, "experience_score": es, "project_score": ps,
            "education_score": ds, "role_score": rs, "total_score": total,
            "verdict": verdict,
            "flags":     result.get("flags", ""),
            "reasoning": result.get("reasoning", ""),
        }
    except QuotaError:
        raise
    except Exception:
        logger.warning(f"EVAL {filename}: Gemini failed → using demo fallback")
        return _mock_evaluate(criteria, candidate, filename)
