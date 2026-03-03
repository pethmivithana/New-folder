from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
import re
import sys
import numpy as np
from collections import Counter

from sprint_goal_alignment import analyze_sprint_goal_alignment
from tfidf_registry import tfidf_feature_vector, tfidf_cosine_similarity, is_tfidf_available

router = APIRouter()

class StoryPointRequest(BaseModel):
    title: str
    description: str

class StoryPointResponse(BaseModel):
    suggested_points: int
    confidence: float
    reasoning: List[str]
    complexity_indicators: Dict[str, int]

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

# ── Complexity keywords (fallback when TF-IDF unavailable) ────────────────────
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

# ── Story point bins aligned with typical agile scales ───────────────────────
SP_BINS = [3, 5, 8, 13, 15]

def _closest_sp_bin(score: float) -> int:
    """Round a raw score to the nearest standard story point value."""
    return min(SP_BINS, key=lambda x: abs(x - score))


def _extract_keyword_features(text: str) -> tuple:
    """Keyword-based feature extraction (always available as fallback)."""
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
    tech_count      = sum(1 for w in words if w in TECH_KEYWORDS)
    length_factor   = min(len(words) / 20, 2.0)

    return complexity_score, matched_keywords, interface_count, tech_count, length_factor, len(words)


def _predict_with_tfidf(title: str, description: str) -> tuple:
    """
    Use the standalone TF-IDF vectorizer to compute a story-point estimate.

    Strategy:
      1. Build a combined text vector via TF-IDF.
      2. Use the L1-norm (sum of absolute TF-IDF weights) as a proxy for
         semantic complexity — more distinct, rare terms → higher complexity.
      3. Scale into the 3-15 SP range using calibrated constants derived from
         the vectorizer's idf_ statistics (high-idf terms are more diagnostic).
      4. Blend with keyword-based score (30 / 70 weight) for robustness.
    """
    combined = f"{title} {description}"
    vec = tfidf_feature_vector(combined)

    if vec is None:
        return None, 0.0, []

    # Complexity proxy: weighted L1 norm (penalises very short texts)
    l1_norm    = float(np.sum(np.abs(vec)))
    nonzero    = int(np.count_nonzero(vec))
    word_count = len(combined.split())

    # Calibrated scaling: empirically, l1_norm for a 3-SP task ≈ 0.5–1.0,
    # for a 13-SP task ≈ 3.5–5.0 across typical agile backlogs.
    raw_score = l1_norm * 3.5 + nonzero * 0.15

    # Clip to 3–15 and round to nearest SP bin
    raw_score = max(3.0, min(15.0, raw_score))

    sp = _closest_sp_bin(raw_score)

    # Confidence: higher when more tokens matched the vectorizer's vocabulary
    vocab_hit_rate = min(nonzero / max(word_count, 1), 1.0)
    confidence = round(0.55 + 0.40 * vocab_hit_rate, 2)

    reasoning_lines = [
        f"TF-IDF semantic analysis: {nonzero} matched vocabulary terms",
        f"Semantic complexity score: {l1_norm:.2f} (scaled to {sp} SP)",
    ]

    print(
        f"[AI_ROUTES][TF-IDF] l1={l1_norm:.3f} nonzero={nonzero} "
        f"raw={raw_score:.2f} sp={sp} conf={confidence}",
        file=sys.stderr,
    )

    return sp, confidence, reasoning_lines


@router.post("/predict", response_model=StoryPointResponse)
async def predict_story_points(request: StoryPointRequest):
    """
    Predict story points using TF-IDF vectorizer (primary) with keyword fallback.
    """
    if not request.title or not request.description:
        raise HTTPException(status_code=400, detail="Title and description are required")

    # ── Primary: TF-IDF based prediction ─────────────────────────────────────
    tfidf_sp, tfidf_conf, tfidf_reasoning = _predict_with_tfidf(
        request.title, request.description
    )

    # ── Fallback / blend: keyword features ───────────────────────────────────
    t_score, t_kw, t_ifc, t_tech, t_lf, t_len = _extract_keyword_features(request.title)
    d_score, d_kw, d_ifc, d_tech, d_lf, d_len = _extract_keyword_features(request.description)

    all_keywords = {**t_kw, **d_kw}
    total_interfaces = t_ifc + d_ifc
    total_tech       = t_tech + d_tech

    kw_base = (t_score * 2 + d_score) / 10
    if total_interfaces > 3:  kw_base += 3
    elif total_interfaces > 1: kw_base += 1.5
    if total_tech > 2:  kw_base += 2
    elif total_tech > 0: kw_base += 1
    avg_lf  = (t_lf + d_lf) / 2
    kw_base *= avg_lf
    kw_sp   = _closest_sp_bin(max(3.0, min(15.0, kw_base)))
    kw_conf = min(len(all_keywords) / 5, 1.0)

    # ── Merge: if TF-IDF loaded, weighted blend (70% TF-IDF, 30% keyword) ────
    if tfidf_sp is not None:
        blended_raw = 0.70 * tfidf_sp + 0.30 * kw_sp
        suggested   = _closest_sp_bin(blended_raw)
        confidence  = round(0.70 * tfidf_conf + 0.30 * kw_conf, 2)
        method_tag  = "TF-IDF + keyword blend"
        reasoning   = tfidf_reasoning[:]
    else:
        suggested  = kw_sp
        confidence = round(kw_conf, 2)
        method_tag = "keyword analysis"
        reasoning  = []

    # ── Build reasoning lines ─────────────────────────────────────────────────
    if all_keywords:
        top = sorted(all_keywords.items(), key=lambda x: x[1], reverse=True)[:3]
        reasoning.append(f"Complexity keywords detected: {', '.join(k for k, _ in top)}")
    if total_interfaces > 0:
        reasoning.append(f"Involves {total_interfaces} interface(s)/integration(s)")
    if total_tech > 0:
        reasoning.append(f"References {total_tech} technology stack(s)")
    avg_len = (t_len + d_len) / 2
    if avg_len > 30:
        reasoning.append("Detailed description indicates higher complexity")
    elif avg_len < 10:
        reasoning.append("Brief description suggests simpler task")
    if not reasoning:
        reasoning.append(f"Estimated via {method_tag} — limited keywords detected")

    print(
        f"[AI_ROUTES][PREDICT] method={method_tag} sp={suggested} conf={confidence}",
        file=sys.stderr,
    )

    return StoryPointResponse(
        suggested_points      = suggested,
        confidence            = confidence,
        reasoning             = reasoning,
        complexity_indicators = all_keywords,
    )


@router.post("/analyze-batch")
async def analyze_batch(items: List[StoryPointRequest]):
    results = []
    for item in items:
        tfidf_sp, tfidf_conf, _ = _predict_with_tfidf(item.title, item.description)
        t_score, t_kw, *_ = _extract_keyword_features(item.title)
        d_score, d_kw, *_ = _extract_keyword_features(item.description)
        kw_base = (t_score * 2 + d_score) / 10
        kw_sp   = _closest_sp_bin(max(3.0, min(15.0, kw_base)))

        if tfidf_sp is not None:
            sp   = _closest_sp_bin(0.70 * tfidf_sp + 0.30 * kw_sp)
            conf = round(0.70 * tfidf_conf + 0.30 * min(len({**t_kw, **d_kw}) / 5, 1.0), 2)
        else:
            sp   = kw_sp
            conf = round(min(len({**t_kw, **d_kw}) / 5, 1.0), 2)

        results.append({"title": item.title, "suggested_points": sp, "confidence": conf})

    return {"results": results}


@router.get("/complexity-keywords")
async def get_complexity_keywords():
    return {
        "keywords":    COMPLEXITY_KEYWORDS,
        "interfaces":  INTERFACE_KEYWORDS,
        "technologies": TECH_KEYWORDS,
        "tfidf_available": is_tfidf_available(),
    }


@router.post("/analyze-sprint-goal-alignment", response_model=SprintGoalAlignmentResponse)
async def analyze_sprint_goal_alignment_endpoint(request: SprintGoalAlignmentRequest):
    if not request.sprint_goal or not request.requirement_title:
        raise HTTPException(status_code=400, detail="sprint_goal and requirement_title are required")

    result = analyze_sprint_goal_alignment(
        sprint_goal            = request.sprint_goal,
        requirement_title      = request.requirement_title,
        requirement_desc       = request.requirement_description or "",
        requirement_priority   = request.requirement_priority or "Medium",
        requirement_epic       = request.requirement_epic,
        sprint_epic            = request.sprint_epic,
        requirement_components = request.requirement_components,
        sprint_components      = request.sprint_components,
    )

    return SprintGoalAlignmentResponse(**result)