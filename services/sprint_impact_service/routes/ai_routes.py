"""
ai_routes.py
────────────────────────────────────────────────────────────────────────────────
FastAPI AI router.

Story Point Suggester — what changed and why:
  1. Bins now use Fibonacci sequence [1,2,3,5,8,13,21] instead of [3,5,8,13,15].
     Why: 15 is not a standard Agile value and capped legitimate large tickets.
     21 is the correct next Fibonacci after 13 and is used on many teams.

  2. Blend weights are now DYNAMIC based on description quality.
     Why: a 2-word description gives TF-IDF almost no signal, so treating it as
     70% of the answer was wrong. Now the TF-IDF weight scales with how much
     useful vocabulary the vectorizer actually found.

  3. Confidence is now genuinely calibrated — can reach below 0.4 (Low).
     Why: the old formula (0.55 + 0.40 × vocab_hit_rate) had a floor of 0.55,
     making the frontend "Low Confidence" badge (threshold < 0.4) unreachable.
     New formula starts at 0.15 and builds from multiple real signals.

  4. A "signal quality" report is returned alongside the suggestion so the
     frontend can show *why* confidence is low (e.g. "description too short").

All other endpoints are UNCHANGED.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
import re
import sys
import json
import os
import numpy as np
from collections import Counter

from sprint_goal_alignment import analyze_sprint_goal_alignment
from tfidf_registry import tfidf_feature_vector, tfidf_cosine_similarity, is_tfidf_available

router = APIRouter()


# ══════════════════════════════════════════════════════════════════════════════
# MODULE 3: SP to Hours Translation Helper (unchanged)
# ══════════════════════════════════════════════════════════════════════════════

def calculate_hours_per_sp(team_pace: float = 1.0) -> float:
    if team_pace <= 0:
        team_pace = 1.0
    return round(8.0 / team_pace, 2)


def format_sp_to_hours(story_points: int, hours_per_sp: float = 8.0) -> str:
    estimated_hours = round(story_points * hours_per_sp, 1)
    return f"{story_points} SP (~{estimated_hours} Hours)"


# ══════════════════════════════════════════════════════════════════════════════
# Sentence-Transformer singleton (unchanged)
# ══════════════════════════════════════════════════════════════════════════════

_st_model = None
_st_model_name = "all-MiniLM-L6-v2"
_st_load_error: Optional[str] = None


def _get_st_model():
    global _st_model, _st_load_error
    if _st_model is not None:
        return _st_model
    if _st_load_error is not None:
        return None
    try:
        from sentence_transformers import SentenceTransformer
        print(f"[ST_ALIGN] Loading '{_st_model_name}'…", file=sys.stderr)
        _st_model = SentenceTransformer(_st_model_name)
        print(f"[ST_ALIGN] '{_st_model_name}' loaded successfully.", file=sys.stderr)
    except Exception as exc:
        _st_load_error = str(exc)
        print(f"[ST_ALIGN] Failed to load '{_st_model_name}': {exc}", file=sys.stderr)
    return _st_model


_get_st_model()


# ══════════════════════════════════════════════════════════════════════════════
# Pydantic models
# ══════════════════════════════════════════════════════════════════════════════

class StoryPointRequest(BaseModel):
    title: str
    description: str

class StoryPointResponse(BaseModel):
    suggested_points: int
    confidence: float
    reasoning: List[str]
    complexity_indicators: Dict[str, int]
    # NEW: tells the frontend what quality signals were found
    signal_quality: Dict[str, object]

class SprintGoalAlignmentRequest(BaseModel):
    sprint_goal: str
    requirement_title: str
    requirement_description: str
    requirement_priority: str
    requirement_epic: Optional[str] = None
    sprint_epic: Optional[str] = None
    requirement_components: Optional[List[str]] = None
    sprint_components: Optional[List[str]] = None

class SprintGoalAlignmentResponse(BaseModel):
    critical_blocker: Dict
    semantic_analysis: Dict
    metadata_analysis: Dict
    final_recommendation: str
    recommendation_reason: str
    next_steps: str

class LLMAlignmentRequest(BaseModel):
    sprint_goal: str
    requirement_title: str
    requirement_description: str
    requirement_priority: str
    requirement_epic: Optional[str] = None
    sprint_epic: Optional[str] = None
    sprint_components: Optional[List[str]] = None
    requirement_components: Optional[List[str]] = None

class LLMAlignmentResponse(BaseModel):
    critical_blocker: Dict
    semantic_analysis: Dict
    metadata_analysis: Dict
    final_recommendation: str
    recommendation_reason: str
    next_steps: str
    engine: str

class STAlignmentRequest(BaseModel):
    sprint_goal: str
    ticket_title: str
    ticket_description: Optional[str] = ""
    priority: str
    ticket_epic: Optional[str] = None
    sprint_epic: Optional[str] = None
    ticket_components: Optional[List[str]] = None
    sprint_components: Optional[List[str]] = None

class STAlignmentResponse(BaseModel):
    is_critical_blocker: bool
    blocker_reason: str
    semantic_score: float
    semantic_score_pct: int
    alignment_category: str
    semantic_reasoning: str
    epic_aligned: bool
    component_overlap: str
    matched_components: List[str]
    metadata_details: str
    alignment_state: str
    alignment_label: str
    model_name: str

class DecisionRequest(BaseModel):
    alignment_state: str
    effort_sp: float
    free_capacity: float
    priority: str
    risk_level: str

class DecisionResponse(BaseModel):
    action: str
    rule_triggered: str
    reasoning: str
    short_title: str

class SimpleAlignmentRequest(BaseModel):
    sprint_goal: str
    task_description: str

class SimpleAlignmentResponse(BaseModel):
    alignment_score: float
    alignment_level: str
    recommendation: str


# ══════════════════════════════════════════════════════════════════════════════
# FIX 1: Proper Fibonacci story point bins
# ══════════════════════════════════════════════════════════════════════════════
#
# OLD: SP_BINS = [3, 5, 8, 13, 15]
#   Problem: 15 is not a standard Agile value. The Fibonacci sequence goes
#   1, 2, 3, 5, 8, 13, 21. Capping at 15 silently downgraded tickets that
#   were genuinely large (e.g. score of 17 → 15, losing signal).
#
# NEW: SP_BINS = [1, 2, 3, 5, 8, 13, 21]
#   1 and 2 are included for completeness; in practice the keyword/TF-IDF
#   scores rarely produce values below 3 for meaningful descriptions.
#   21 correctly represents large, complex tickets that should probably be
#   split — which is communicated via a reasoning message.
#
SP_BINS = [1, 2, 3, 5, 8, 13, 21]

def _closest_sp_bin(score: float) -> int:
    """Snap a raw numeric score to the nearest Fibonacci story point bin."""
    return min(SP_BINS, key=lambda x: abs(x - score))


# ══════════════════════════════════════════════════════════════════════════════
# Complexity keywords (unchanged)
# ══════════════════════════════════════════════════════════════════════════════

COMPLEXITY_KEYWORDS = {
    "algorithm": 8, "optimization": 7, "migration": 7, "refactor": 6,
    "integration": 7, "api": 5, "database": 6, "authentication": 7,
    "authorization": 7, "security": 7, "performance": 6, "scalability": 7,
    "architecture": 8, "framework": 6, "third-party": 6, "multiple": 5,
    "complex": 7, "implement": 4, "create": 3, "add": 3, "update": 4,
    "modify": 4, "enhance": 4, "improve": 4, "feature": 4, "component": 4,
    "service": 5, "endpoint": 4, "validation": 4, "testing": 4,
    "fix": 2, "bug": 2, "typo": 1, "change": 2, "remove": 2, "delete": 2,
    "simple": 2, "minor": 2, "small": 2, "text": 2, "label": 2,
    "styling": 2, "css": 2, "ui": 3,
}

INTERFACE_KEYWORDS = [
    "frontend", "backend", "ui", "ux", "interface", "screen",
    "page", "form", "modal", "dialog", "api", "endpoint",
    "rest", "graphql", "websocket", "microservice"
]

TECH_KEYWORDS = [
    "react", "vue", "angular", "node", "python", "java",
    "mongodb", "postgresql", "mysql", "redis", "docker",
    "kubernetes", "aws", "azure", "gcp"
]


def _extract_keyword_features(text: str) -> tuple:
    text_lower = text.lower()
    text_clean = re.sub(r'[^a-zA-Z0-9\s]', ' ', text_lower)
    words = text_clean.split()
    complexity_score = 0
    matched_keywords: Dict[str, int] = {}
    for word in words:
        if word in COMPLEXITY_KEYWORDS:
            complexity_score += COMPLEXITY_KEYWORDS[word]
            matched_keywords[word] = matched_keywords.get(word, 0) + 1
    interface_count = sum(1 for w in words if w in INTERFACE_KEYWORDS)
    tech_count = sum(1 for w in words if w in TECH_KEYWORDS)
    length_factor = min(len(words) / 20, 2.0)
    return complexity_score, matched_keywords, interface_count, tech_count, length_factor, len(words)


# ══════════════════════════════════════════════════════════════════════════════
# FIX 2 + 3: Dynamic blending and calibrated confidence
# ══════════════════════════════════════════════════════════════════════════════
#
# OLD _predict_with_tfidf():
#   - Always returned confidence = 0.55 + 0.40 × vocab_hit_rate
#   - Floor was 0.55 → frontend "Low Confidence" badge (< 0.4) was impossible
#   - Did not report how sparse the vocabulary match was
#
# NEW _predict_with_tfidf():
#   - Returns raw signals: l1_norm, nonzero, word_count, vocab_hit_rate
#   - Caller (_blend_predictions) decides how much to trust TF-IDF
#   - No confidence computed here — done in _blend_predictions
#
def _predict_with_tfidf_raw(title: str, description: str) -> Optional[Dict]:
    """
    Returns raw TF-IDF signals without computing a final SP or confidence.
    Returns None if the vectorizer is unavailable.
    """
    combined = f"{title} {description}"
    vec = tfidf_feature_vector(combined)
    if vec is None:
        return None

    l1_norm = float(np.sum(np.abs(vec)))
    nonzero = int(np.count_nonzero(vec))
    word_count = len(combined.split())
    vocab_hit_rate = min(nonzero / max(word_count, 1), 1.0)

    # Raw score before binning — same formula as before
    raw_score = max(1.0, min(21.0, l1_norm * 3.5 + nonzero * 0.15))
    sp = _closest_sp_bin(raw_score)

    print(
        f"[AI_ROUTES][TF-IDF raw] l1={l1_norm:.3f} nonzero={nonzero} "
        f"words={word_count} vocab_hit={vocab_hit_rate:.3f} raw={raw_score:.2f} sp={sp}",
        file=sys.stderr,
    )

    return {
        "sp": sp,
        "raw_score": raw_score,
        "l1_norm": l1_norm,
        "nonzero": nonzero,
        "word_count": word_count,
        "vocab_hit_rate": vocab_hit_rate,
    }


def _compute_keyword_sp(
    title: str,
    description: str,
) -> Dict:
    """
    Compute a story point estimate from keyword analysis alone.
    Returns the SP and intermediate scoring data for blending.
    """
    t_score, t_kw, t_ifc, t_tech, t_lf, t_len = _extract_keyword_features(title)
    d_score, d_kw, d_ifc, d_tech, d_lf, d_len = _extract_keyword_features(description)

    all_keywords = {**t_kw, **d_kw}
    total_interfaces = t_ifc + d_ifc
    total_tech = t_tech + d_tech

    kw_base = (t_score * 2 + d_score) / 10
    if total_interfaces > 3:   kw_base += 3
    elif total_interfaces > 1: kw_base += 1.5
    if total_tech > 2:  kw_base += 2
    elif total_tech > 0: kw_base += 1

    avg_lf = (t_lf + d_lf) / 2
    kw_base *= avg_lf
    kw_base = max(1.0, min(21.0, kw_base))
    sp = _closest_sp_bin(kw_base)

    # Keyword signal strength: how many keywords matched relative to total words
    total_words = max(t_len + d_len, 1)
    kw_density = min(len(all_keywords) / total_words * 10, 1.0)

    return {
        "sp": sp,
        "raw_score": kw_base,
        "all_keywords": all_keywords,
        "total_interfaces": total_interfaces,
        "total_tech": total_tech,
        "kw_density": kw_density,
        "t_len": t_len,
        "d_len": d_len,
    }


def _blend_predictions(
    tfidf: Optional[Dict],
    kw: Dict,
    title: str,
    description: str,
) -> tuple:
    """
    FIX 2: Dynamic blend weight based on description richness.

    Old behaviour: always 70% TF-IDF, 30% keyword regardless of input quality.

    New behaviour:
      - tfidf_weight scales with vocab_hit_rate and description word count.
        A 2-word description gets ~25% TF-IDF weight.
        A 30-word description with good vocabulary gets ~75% TF-IDF weight.
      - keyword_weight = 1 - tfidf_weight.

    FIX 3: Calibrated confidence — can genuinely reach below 0.4.

    Old formula: 0.55 + 0.40 × vocab_hit_rate  (floor = 0.55, unreachable low)

    New formula starts from 0.15 (almost nothing) and adds:
      +0.20 if TF-IDF vocabulary hit rate > 0.15  (vectorizer found matches)
      +0.15 if description has 10+ words           (meaningful input)
      +0.15 if description has 20+ words           (detailed input)
      +0.10 if keyword density is high             (domain terms present)
      +0.10 if TF-IDF and keywords agree closely   (both signals align)
      +0.10 if not a large ticket (21 SP) where uncertainty is higher
    Max is ~0.95 when all signals fire.

    Returns: (suggested_sp, confidence, signal_quality_dict, reasoning_lines)
    """
    desc_words = len(description.split()) if description else 0
    title_words = len(title.split()) if title else 0

    # ── Determine TF-IDF blend weight ──────────────────────────────────────────
    if tfidf is None:
        tfidf_weight = 0.0
        kw_weight = 1.0
    else:
        # Base weight from vocab hit rate — scales from 0.25 to 0.75
        # vocab_hit_rate=0 → weight=0.25, vocab_hit_rate=1 → weight=0.75
        base_tfidf_weight = 0.25 + 0.50 * tfidf["vocab_hit_rate"]

        # Reduce TF-IDF weight if description is sparse
        # Below 10 words: TF-IDF has very little to work with
        if desc_words < 5:
            base_tfidf_weight *= 0.35
        elif desc_words < 10:
            base_tfidf_weight *= 0.60
        elif desc_words < 20:
            base_tfidf_weight *= 0.85

        tfidf_weight = round(min(0.80, max(0.20, base_tfidf_weight)), 3)
        kw_weight = round(1.0 - tfidf_weight, 3)

    # ── Blend the SP scores ────────────────────────────────────────────────────
    if tfidf is not None:
        blended_raw = tfidf_weight * tfidf["raw_score"] + kw_weight * kw["raw_score"]
    else:
        blended_raw = kw["raw_score"]

    suggested_sp = _closest_sp_bin(blended_raw)

    # ── Calibrated confidence ──────────────────────────────────────────────────
    confidence = 0.15  # start near zero — must earn it

    # Signal 1: TF-IDF found matching vocabulary
    if tfidf is not None and tfidf["vocab_hit_rate"] > 0.15:
        confidence += 0.20

    # Signal 2: Description has enough words to be meaningful
    if desc_words >= 10:
        confidence += 0.15
    if desc_words >= 20:
        confidence += 0.15

    # Signal 3: Strong keyword domain signal
    if kw["kw_density"] > 0.2:
        confidence += 0.10

    # Signal 4: TF-IDF and keyword methods agree (within 1 bin distance)
    if tfidf is not None:
        if abs(tfidf["sp"] - kw["sp"]) <= 1:
            confidence += 0.10

    # Signal 5: Not at the uncertainty ceiling (21 SP)
    if suggested_sp < 21:
        confidence += 0.10

    # Signal 6: Title has at least 3 words (not just a one-word label)
    if title_words >= 3:
        confidence += 0.05

    confidence = round(min(0.95, confidence), 2)

    # ── Signal quality report (sent to frontend) ───────────────────────────────
    signal_quality = {
        "tfidf_available": tfidf is not None,
        "tfidf_weight_used": tfidf_weight,
        "keyword_weight_used": kw_weight,
        "description_word_count": desc_words,
        "vocab_hit_rate": round(tfidf["vocab_hit_rate"], 3) if tfidf else 0.0,
        "keyword_density": round(kw["kw_density"], 3),
        "methods_agreed": (tfidf is not None and abs(tfidf["sp"] - kw["sp"]) <= 1),
        "confidence_notes": _confidence_notes(tfidf, kw, desc_words, suggested_sp),
    }

    # ── Reasoning lines ────────────────────────────────────────────────────────
    reasoning = []
    if tfidf is not None:
        reasoning.append(
            f"TF-IDF analysis: {tfidf['nonzero']} vocabulary matches "
            f"(weight: {int(tfidf_weight * 100)}%)"
        )
    if kw["all_keywords"]:
        top = sorted(kw["all_keywords"].items(), key=lambda x: x[1], reverse=True)[:3]
        reasoning.append(f"Complexity keywords: {', '.join(k for k, _ in top)}")
    if kw["total_interfaces"] > 0:
        reasoning.append(f"Involves {kw['total_interfaces']} interface/integration(s)")
    if kw["total_tech"] > 0:
        reasoning.append(f"References {kw['total_tech']} technology stack(s)")
    if desc_words >= 20:
        reasoning.append("Detailed description — higher estimate confidence")
    elif desc_words < 10:
        reasoning.append("Short description — add more detail to improve accuracy")
    if suggested_sp == 21:
        reasoning.append("Estimated at 21 SP — consider splitting this ticket")

    if not reasoning:
        reasoning.append("Limited signal — add title keywords and a description")

    print(
        f"[AI_ROUTES][BLEND] tfidf_w={tfidf_weight} kw_w={kw_weight} "
        f"sp={suggested_sp} conf={confidence}",
        file=sys.stderr,
    )

    return suggested_sp, confidence, signal_quality, reasoning


def _confidence_notes(tfidf, kw, desc_words, suggested_sp) -> List[str]:
    """Human-readable list of what's driving confidence up or down."""
    notes = []
    if tfidf is None:
        notes.append("TF-IDF vectorizer not available — keyword-only estimate")
    elif tfidf["vocab_hit_rate"] < 0.15:
        notes.append("Low vocabulary overlap with training data")
    if desc_words < 10:
        notes.append("Description is too short for high confidence")
    if tfidf is not None and abs(tfidf["sp"] - kw["sp"]) > 1:
        notes.append(
            f"Methods disagree: TF-IDF suggests {tfidf['sp']} SP, "
            f"keywords suggest {kw['sp']} SP"
        )
    if suggested_sp == 21:
        notes.append("Large ticket — estimates at this size carry high uncertainty")
    if not notes:
        notes.append("All signals present and consistent")
    return notes


# ══════════════════════════════════════════════════════════════════════════════
# Endpoints
# ══════════════════════════════════════════════════════════════════════════════

@router.post("/predict", response_model=StoryPointResponse)
async def predict_story_points(request: StoryPointRequest):
    """
    Predict story points using TF-IDF + keyword analysis with dynamic blending.

    Changes from the old version:
      - Bins: [1,2,3,5,8,13,21] instead of [3,5,8,13,15]
      - TF-IDF weight scales with description richness (was hardcoded 70%)
      - Confidence is calibrated from 0.15 upward (was floored at 0.55)
      - signal_quality field added for frontend transparency
    """
    if not request.title or not request.description:
        raise HTTPException(status_code=400, detail="Title and description are required")

    tfidf = _predict_with_tfidf_raw(request.title, request.description)
    kw = _compute_keyword_sp(request.title, request.description)

    suggested_sp, confidence, signal_quality, reasoning = _blend_predictions(
        tfidf, kw, request.title, request.description
    )

    return StoryPointResponse(
        suggested_points=suggested_sp,
        confidence=confidence,
        reasoning=reasoning,
        complexity_indicators=kw["all_keywords"],
        signal_quality=signal_quality,
    )


@router.post("/analyze-batch")
async def analyze_batch(items: List[StoryPointRequest]):
    results = []
    for item in items:
        tfidf = _predict_with_tfidf_raw(item.title, item.description)
        kw = _compute_keyword_sp(item.title, item.description)
        sp, conf, sq, _ = _blend_predictions(tfidf, kw, item.title, item.description)
        results.append({
            "title": item.title,
            "suggested_points": sp,
            "confidence": conf,
            "signal_quality": sq,
        })
    return {"results": results}


@router.get("/complexity-keywords")
async def get_complexity_keywords():
    return {
        "keywords": COMPLEXITY_KEYWORDS,
        "interfaces": INTERFACE_KEYWORDS,
        "technologies": TECH_KEYWORDS,
        "tfidf_available": is_tfidf_available(),
        "sp_bins": SP_BINS,
    }


# ── All alignment / decision endpoints below are UNCHANGED ────────────────────

@router.post("/analyze-sprint-goal-alignment", response_model=SprintGoalAlignmentResponse)
async def analyze_sprint_goal_alignment_endpoint(request: SprintGoalAlignmentRequest):
    if not request.sprint_goal or not request.requirement_title:
        raise HTTPException(status_code=400, detail="sprint_goal and requirement_title are required")
    result = analyze_sprint_goal_alignment(
        sprint_goal=request.sprint_goal,
        requirement_title=request.requirement_title,
        requirement_desc=request.requirement_description or "",
        requirement_priority=request.requirement_priority or "Medium",
        requirement_epic=request.requirement_epic,
        sprint_epic=request.sprint_epic,
        requirement_components=request.requirement_components,
        sprint_components=request.sprint_components,
    )
    return SprintGoalAlignmentResponse(**result)


_LLM_SYSTEM_PROMPT = """You are an AI Scrum Master assistant. Your task is to analyze whether a new requirement should be accepted into an active sprint based on its alignment with the sprint goal. You will evaluate the requirement using a layered, research-validated approach combining semantic analysis, metadata traceability, and critical blocker detection.

Input Data:
* Sprint Goal: [The official sprint goal statement]
* Requirement Title: [Title of the new requirement]
* Requirement Description: [Full description text]
* Requirement Priority: [Critical/Blocker/High/Medium/Low]
* Requirement Epic: [Epic name this requirement belongs to]
* Sprint Epic: [Primary epic focus of current sprint]
* Sprint Component Tags: [List of technical components in sprint]
* Requirement Component Tags: [List of components this requirement touches]

Layer 1: Critical Blocker Detection
Rule: Flag as CRITICAL BLOCKER if keywords indicate production outage/security breach AND Priority = Critical/Blocker.

Layer 2: Semantic Similarity Analysis
* Score > 0.7 (HIGHLY RELEVANT): Directly contributes to goal.
* Score 0.4 - 0.7 (TANGENTIAL): Related themes but addresses a different aspect.
* Score < 0.4 (UNRELATED): Completely outside the scope.

Layer 3: Metadata Traceability Check
Check Epic alignment and Component overlap.

Layer 4: Integrated Recommendation
* ACCEPT: If Layer 1 is a blocker OR Layer 2 > 0.7.
* CONSIDER: If Layer 2 is 0.4 - 0.7 AND strong metadata overlap.
* EVALUATE: If Layer 2 is 0.4 - 0.7 AND weak metadata overlap.
* DEFER: If Layer 2 < 0.4.

Output Format (Strict JSON only — no markdown, no explanation outside the JSON object):
{
  "critical_blocker": {"detected": true/false, "reason": "..."},
  "semantic_analysis": {"alignment_category": "HIGHLY_RELEVANT|TANGENTIAL|UNRELATED", "reasoning": "..."},
  "metadata_analysis": {"epic_aligned": true/false, "component_overlap": "high|medium|low|none", "details": "..."},
  "final_recommendation": "ACCEPT|DEFER|CONSIDER|EVALUATE",
  "recommendation_reason": "...",
  "next_steps": "..."
}"""


def _build_llm_user_message(req: LLMAlignmentRequest) -> str:
    sprint_comp_str = ", ".join(req.sprint_components) if req.sprint_components else "Not specified"
    req_comp_str = ", ".join(req.requirement_components) if req.requirement_components else "Not specified"
    return f"""Please analyze the following requirement for sprint inclusion:

* Sprint Goal: {req.sprint_goal}
* Requirement Title: {req.requirement_title}
* Requirement Description: {req.requirement_description or 'Not provided'}
* Requirement Priority: {req.requirement_priority}
* Requirement Epic: {req.requirement_epic or 'Not specified'}
* Sprint Epic: {req.sprint_epic or 'Not specified'}
* Sprint Component Tags: {sprint_comp_str}
* Requirement Component Tags: {req_comp_str}

Respond strictly with the JSON object described in the system prompt. No markdown fences. No preamble."""


def _parse_llm_json(raw_text: str) -> dict:
    text = raw_text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        inner = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
        text = "\n".join(inner).strip()
    parsed = json.loads(text)
    required_keys = {
        "critical_blocker", "semantic_analysis", "metadata_analysis",
        "final_recommendation", "recommendation_reason", "next_steps",
    }
    missing = required_keys - set(parsed.keys())
    if missing:
        raise ValueError(f"LLM JSON missing required keys: {missing}")
    return parsed


async def _call_gemini(user_message: str) -> dict:
    try:
        import google.generativeai as genai
    except ImportError:
        raise RuntimeError("google-generativeai not installed.")
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=_LLM_SYSTEM_PROMPT,
        generation_config=genai.types.GenerationConfig(temperature=0.1, max_output_tokens=800),
    )
    response = model.generate_content(user_message)
    return _parse_llm_json(response.text)


async def _call_openai(user_message: str) -> dict:
    try:
        from openai import AsyncOpenAI
    except ImportError:
        raise RuntimeError("openai not installed.")
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")
    client = AsyncOpenAI(api_key=api_key)
    completion = await client.chat.completions.create(
        model="gpt-4o-mini", temperature=0.1, max_tokens=800,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": _LLM_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    )
    return _parse_llm_json(completion.choices[0].message.content)


def _fallback_classical(req: LLMAlignmentRequest, reason: str) -> dict:
    result = analyze_sprint_goal_alignment(
        sprint_goal=req.sprint_goal,
        requirement_title=req.requirement_title,
        requirement_desc=req.requirement_description or "",
        requirement_priority=req.requirement_priority or "Medium",
        requirement_epic=req.requirement_epic,
        sprint_epic=req.sprint_epic,
        requirement_components=req.requirement_components,
        sprint_components=req.sprint_components,
    )
    result["engine"] = "fallback_classical"
    return result


@router.post("/align-sprint-goal", response_model=LLMAlignmentResponse)
async def align_sprint_goal_llm(request: LLMAlignmentRequest):
    if not request.sprint_goal or not request.requirement_title:
        raise HTTPException(status_code=400, detail="sprint_goal and requirement_title are required")
    user_message = _build_llm_user_message(request)
    failure_reason = "no LLM API keys configured"
    if os.environ.get("GEMINI_API_KEY", "").strip():
        try:
            parsed = await _call_gemini(user_message)
            parsed["engine"] = "gemini"
            return LLMAlignmentResponse(**parsed)
        except Exception as exc:
            failure_reason = f"Gemini failed: {exc}"
    if os.environ.get("OPENAI_API_KEY", "").strip():
        try:
            parsed = await _call_openai(user_message)
            parsed["engine"] = "openai"
            return LLMAlignmentResponse(**parsed)
        except Exception as exc:
            failure_reason = f"OpenAI failed: {exc}"
    fallback = _fallback_classical(request, failure_reason)
    return LLMAlignmentResponse(**fallback)


_ST_BLOCKER_KEYWORDS = {
    "crash", "crashed", "down", "outage", "broken", "not working",
    "emergency", "hotfix", "production issue", "security breach",
    "data loss", "data leak", "payment failure", "site down", "service down",
    "incident", "p0", "sev1", "sev 1",
}

_ST_BLOCKER_PRIORITIES = {"critical", "blocker"}
_ST_HIGHLY_RELEVANT_THRESHOLD = 0.55
_ST_TANGENTIAL_THRESHOLD = 0.35


def _st_layer1_blocker(title: str, description: str, priority: str) -> tuple:
    if priority.strip().lower() not in _ST_BLOCKER_PRIORITIES:
        return False, f"Priority '{priority}' is not Critical or Blocker."
    combined = f"{title} {description}".lower()
    found = [kw for kw in _ST_BLOCKER_KEYWORDS if kw in combined]
    if found:
        return True, f"Production-emergency keywords detected with {priority} priority: {', '.join(found)}."
    return False, f"Priority is {priority} but no production-emergency keywords found."


def _st_layer2_semantic(model, sprint_goal: str, ticket_text: str) -> tuple:
    from sentence_transformers import util as st_util
    embeddings = model.encode([sprint_goal, ticket_text], convert_to_tensor=True)
    cos_score = float(st_util.cos_sim(embeddings[0], embeddings[1]).item())
    cos_score = round(max(0.0, min(1.0, cos_score)), 4)
    if cos_score >= _ST_HIGHLY_RELEVANT_THRESHOLD:
        category = "HIGHLY_RELEVANT"
        reasoning = (
            f"Cosine similarity {cos_score:.2f} ≥ {_ST_HIGHLY_RELEVANT_THRESHOLD}. "
            "Ticket is semantically close to the sprint goal."
        )
    elif cos_score >= _ST_TANGENTIAL_THRESHOLD:
        category = "TANGENTIAL"
        reasoning = (
            f"Cosine similarity {cos_score:.2f} is between thresholds. "
            "Ticket shares related themes but does not directly advance the sprint goal."
        )
    else:
        category = "UNRELATED"
        reasoning = f"Cosine similarity {cos_score:.2f} < {_ST_TANGENTIAL_THRESHOLD}. Semantically distant."
    return cos_score, category, reasoning


def _st_layer3_metadata(ticket_epic, sprint_epic, ticket_components, sprint_components) -> tuple:
    t_epic = (ticket_epic or "").strip().lower()
    s_epic = (sprint_epic or "").strip().lower()
    epic_aligned = bool(t_epic and s_epic and t_epic == s_epic)
    t_comps = {c.strip().lower() for c in (ticket_components or []) if c.strip()}
    s_comps = {c.strip().lower() for c in (sprint_components or []) if c.strip()}
    matched = sorted(t_comps & s_comps)
    overlap = len(matched)
    total_s = len(s_comps) if s_comps else 1
    ratio = overlap / total_s
    if ratio >= 0.66:
        level = "high"
        details = f"Strong component match: {overlap}/{total_s} sprint components covered."
    elif ratio >= 0.33:
        level = "medium"
        details = f"Moderate component match: {overlap}/{total_s} sprint components covered."
    elif overlap > 0:
        level = "low"
        details = f"Weak component match: {overlap}/{total_s} sprint components covered."
    else:
        level = "none"
        details = "No component overlap."
    if epic_aligned:
        details += f" Epic '{t_epic}' matches sprint epic."
    elif t_epic and s_epic:
        details += f" Epic mismatch: ticket='{t_epic}' vs sprint='{s_epic}'."
    return epic_aligned, level, matched, details


@router.post("/st-align-sprint-goal", response_model=STAlignmentResponse)
async def st_align_sprint_goal(request: STAlignmentRequest):
    if not request.sprint_goal or not request.ticket_title:
        raise HTTPException(status_code=400, detail="sprint_goal and ticket_title are required.")
    model = _get_st_model()
    if model is None:
        raise HTTPException(status_code=503, detail=f"Sentence-Transformer not available: {_st_load_error}")

    is_blocker, blocker_reason = _st_layer1_blocker(
        request.ticket_title, request.ticket_description or "", request.priority
    )
    ticket_text = f"{request.ticket_title} {request.ticket_description or ''}".strip()
    semantic_score, category, semantic_reasoning = _st_layer2_semantic(
        model, request.sprint_goal, ticket_text
    )
    epic_aligned, component_overlap, matched_components, metadata_details = _st_layer3_metadata(
        request.ticket_epic, request.sprint_epic,
        request.ticket_components, request.sprint_components,
    )

    strong_metadata = epic_aligned or component_overlap in ("high", "medium")
    if is_blocker:
        alignment_state = "CRITICAL_BLOCKER"
        alignment_label = "🚨 Critical Blocker"
    elif category == "HIGHLY_RELEVANT":
        alignment_state = "STRONGLY_ALIGNED"
        alignment_label = "🎯 Strongly Aligned"
    elif category == "TANGENTIAL" and strong_metadata:
        alignment_state = "PARTIALLY_ALIGNED"
        alignment_label = "🔵 Partially Aligned"
    elif category == "TANGENTIAL" and not strong_metadata:
        alignment_state = "WEAKLY_ALIGNED"
        alignment_label = "🟡 Weakly Aligned"
    else:
        alignment_state = "UNALIGNED"
        alignment_label = "🔴 Unaligned"

    return STAlignmentResponse(
        is_critical_blocker=is_blocker,
        blocker_reason=blocker_reason,
        semantic_score=semantic_score,
        semantic_score_pct=int(round(semantic_score * 100)),
        alignment_category=category,
        semantic_reasoning=semantic_reasoning,
        epic_aligned=epic_aligned,
        component_overlap=component_overlap,
        matched_components=matched_components,
        metadata_details=metadata_details,
        alignment_state=alignment_state,
        alignment_label=alignment_label,
        model_name=_st_model_name,
    )


@router.post("/decide", response_model=DecisionResponse)
async def decide(request: DecisionRequest):
    from decision_engine import calculate_agile_recommendation
    result = calculate_agile_recommendation(
        alignment_state=request.alignment_state,
        effort_sp=request.effort_sp,
        free_capacity=request.free_capacity,
        priority=request.priority,
        risk_level=request.risk_level,
    )
    return DecisionResponse(**result.to_dict())


@router.post("/align-simple-goal", response_model=SimpleAlignmentResponse)
async def align_simple_goal(request: SimpleAlignmentRequest):
    if not request.sprint_goal or not request.task_description:
        raise HTTPException(status_code=400, detail="sprint_goal and task_description are required.")
    if not is_tfidf_available():
        raise HTTPException(status_code=503, detail="TF-IDF vectorizer not loaded.")
    alignment_score = tfidf_cosine_similarity(request.sprint_goal, request.task_description)
    if alignment_score < 0:
        raise HTTPException(status_code=503, detail="TF-IDF similarity computation failed.")
    if alignment_score >= 0.5:
        alignment_level = "STRONGLY_ALIGNED"
        recommendation = f"Task is strongly aligned (score: {alignment_score:.2f}). Safe to add."
    elif alignment_score >= 0.3:
        alignment_level = "PARTIALLY_ALIGNED"
        recommendation = f"Task is partially aligned (score: {alignment_score:.2f}). Review before adding."
    else:
        alignment_level = "UNALIGNED"
        recommendation = f"Task is not well aligned (score: {alignment_score:.2f}). Likely scope creep."
    return SimpleAlignmentResponse(
        alignment_score=round(alignment_score, 4),
        alignment_level=alignment_level,
        recommendation=recommendation,
    )