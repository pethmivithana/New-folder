"""
ai_routes.py
────────────────────────────────────────────────────────────────────────────────
FastAPI AI router.

Endpoints (all pre-existing are UNCHANGED):
  POST /predict                        – TF-IDF story-point suggestion
  POST /analyze-batch                  – batch story-point suggestion
  GET  /complexity-keywords            – keyword dictionary introspection
  POST /analyze-sprint-goal-alignment  – classical TF-IDF / Jaccard alignment
  POST /align-sprint-goal              – LLM-based alignment (Gemini → OpenAI → fallback)
  POST /st-align-sprint-goal           – Phase 1: Sentence-Transformer alignment state only
  POST /decide                         – Phase 3: Decision Engine (ADD|DEFER|SPLIT|SWAP)
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
# MODULE 3: SP to Hours Translation Helper (Global TEAM_PACE)
# ══════════════════════════════════════════════════════════════════════════════

def calculate_hours_per_sp(team_pace: float = 1.0) -> float:
    """
    Calculate hours per story point using TEAM_PACE.
    
    Formula: hours_per_sp = 8 / TEAM_PACE
    
    Args:
        team_pace (float): Story points per development day (from analytics)
    
    Returns:
        float: Hours required per story point
    """
    if team_pace <= 0:
        team_pace = 1.0
    return round(8.0 / team_pace, 2)


def format_sp_to_hours(story_points: int, hours_per_sp: float = 8.0) -> str:
    """
    Format story points with hours translation for display.
    
    Example: format_sp_to_hours(5, 8.0) → "5 SP (~40 Hours)"
    
    Args:
        story_points (int): Number of story points
        hours_per_sp (float): Hours per story point
    
    Returns:
        str: Formatted display string
    """
    estimated_hours = round(story_points * hours_per_sp, 1)
    return f"{story_points} SP (~{estimated_hours} Hours)"


# ══════════════════════════════════════════════════════════════════════════════
# MODULE 4: Semantic Sprint Alignment (TF-IDF based, no LLM required)
# ══════════════════════════════════════════════════════════════════════════════

class SimpleAlignmentRequest(BaseModel):
    """Simple TF-IDF based sprint goal alignment (MODULE 4)"""
    sprint_goal: str
    task_description: str

class SimpleAlignmentResponse(BaseModel):
    """Simple alignment score (0-1), no action recommendations"""
    alignment_score: float  # 0-1
    alignment_level: str    # "STRONGLY_ALIGNED" | "PARTIALLY_ALIGNED" | "UNALIGNED"
    recommendation: str     # Human-readable feedback


# ══════════════════════════════════════════════════════════════════════════════
# Sentence-Transformer singleton  (loaded once at module import)
# ══════════════════════════════════════════════════════════════════════════════

_st_model = None
_st_model_name = "all-MiniLM-L6-v2"
_st_load_error: Optional[str] = None


def _get_st_model():
    """
    Return the cached SentenceTransformer instance, loading it on first call.
    If sentence-transformers is not installed or the model can't be fetched,
    _st_load_error is set and None is returned – the endpoint falls back
    gracefully instead of crashing startup.
    """
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


# Trigger load at import time so it is warm on first request
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

# LLM-based alignment (previous session)
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

# ── Sentence-Transformer alignment (Phase 1) ──────────────────────────────────
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
    # Layer 1
    is_critical_blocker: bool
    blocker_reason: str
    # Layer 2
    semantic_score: float          # cosine similarity rounded to 4dp, 0–1
    semantic_score_pct: int        # 0–100 for the UI percentage badge
    alignment_category: str        # HIGHLY_RELEVANT | TANGENTIAL | UNRELATED (internal L2 bucket)
    semantic_reasoning: str
    # Layer 3
    epic_aligned: bool
    component_overlap: str         # high | medium | low | none
    matched_components: List[str]
    metadata_details: str
    # Phase 1 output — NO action verbs, purely descriptive alignment state
    alignment_state: str           # CRITICAL_BLOCKER | STRONGLY_ALIGNED | PARTIALLY_ALIGNED | WEAKLY_ALIGNED | UNALIGNED
    alignment_label: str           # Human-readable emoji label for the UI
    # Metadata
    model_name: str

# ── Phase 3 Decision Engine ───────────────────────────────────────────────────
class DecisionRequest(BaseModel):
    alignment_state: str           # from Phase 1 STAlignmentResponse.alignment_state
    effort_sp: float               # from Phase 2 ML effort model
    free_capacity: float           # team_velocity - current_load
    priority: str                  # Low | Medium | High | Critical
    risk_level: str                # LOW | MEDIUM | HIGH (derived from schedule risk probability)

class DecisionResponse(BaseModel):
    action: str                    # ADD | DEFER | SPLIT | SWAP
    rule_triggered: str            # human-readable rule name
    reasoning: str                 # full explanation for the UI card
    short_title: str               # one-line label for the card header


# ══════════════════════════════════════════════════════════════════════════════
# Complexity keywords & helpers  (unchanged from previous sessions)
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

SP_BINS = [3, 5, 8, 13, 15]

def _closest_sp_bin(score: float) -> int:
    return min(SP_BINS, key=lambda x: abs(x - score))


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
    tech_count      = sum(1 for w in words if w in TECH_KEYWORDS)
    length_factor   = min(len(words) / 20, 2.0)
    return complexity_score, matched_keywords, interface_count, tech_count, length_factor, len(words)


def _predict_with_tfidf(title: str, description: str) -> tuple:
    combined = f"{title} {description}"
    vec = tfidf_feature_vector(combined)
    if vec is None:
        return None, 0.0, []
    l1_norm    = float(np.sum(np.abs(vec)))
    nonzero    = int(np.count_nonzero(vec))
    word_count = len(combined.split())
    raw_score  = l1_norm * 3.5 + nonzero * 0.15
    raw_score  = max(3.0, min(15.0, raw_score))
    sp         = _closest_sp_bin(raw_score)
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


# ══════════════════════════════════════════════════════════════════════════════
# Existing endpoints  (ALL UNCHANGED)
# ══════════════════════════════════════════════════════════════════════════════

@router.post("/predict", response_model=StoryPointResponse)
async def predict_story_points(request: StoryPointRequest):
    """Predict story points using TF-IDF vectorizer (primary) with keyword fallback."""
    if not request.title or not request.description:
        raise HTTPException(status_code=400, detail="Title and description are required")

    tfidf_sp, tfidf_conf, tfidf_reasoning = _predict_with_tfidf(
        request.title, request.description
    )

    t_score, t_kw, t_ifc, t_tech, t_lf, t_len = _extract_keyword_features(request.title)
    d_score, d_kw, d_ifc, d_tech, d_lf, d_len = _extract_keyword_features(request.description)

    all_keywords     = {**t_kw, **d_kw}
    total_interfaces = t_ifc + d_ifc
    total_tech       = t_tech + d_tech

    kw_base = (t_score * 2 + d_score) / 10
    if total_interfaces > 3:   kw_base += 3
    elif total_interfaces > 1: kw_base += 1.5
    if total_tech > 2:  kw_base += 2
    elif total_tech > 0: kw_base += 1
    avg_lf  = (t_lf + d_lf) / 2
    kw_base *= avg_lf
    kw_sp   = _closest_sp_bin(max(3.0, min(15.0, kw_base)))
    kw_conf = min(len(all_keywords) / 5, 1.0)

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

    print(f"[AI_ROUTES][PREDICT] method={method_tag} sp={suggested} conf={confidence}", file=sys.stderr)

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
        "keywords":        COMPLEXITY_KEYWORDS,
        "interfaces":      INTERFACE_KEYWORDS,
        "technologies":    TECH_KEYWORDS,
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


# ── LLM endpoint (previous session, unchanged) ───��────────────────────────────

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
    sprint_comp_str = ", ".join(req.sprint_components)       if req.sprint_components       else "Not specified"
    req_comp_str    = ", ".join(req.requirement_components)  if req.requirement_components  else "Not specified"
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
        text  = "\n".join(inner).strip()
    parsed = json.loads(text)
    required_keys = {
        "critical_blocker", "semantic_analysis", "metadata_analysis",
        "final_recommendation", "recommendation_reason", "next_steps",
    }
    missing = required_keys - set(parsed.keys())
    if missing:
        raise ValueError(f"LLM JSON missing required keys: {missing}")
    cb = parsed["critical_blocker"]
    if "detected" not in cb or "reason" not in cb:
        raise ValueError("critical_blocker must contain 'detected' and 'reason'")
    sa = parsed["semantic_analysis"]
    if "alignment_category" not in sa or "reasoning" not in sa:
        raise ValueError("semantic_analysis must contain 'alignment_category' and 'reasoning'")
    ma = parsed["metadata_analysis"]
    if not all(k in ma for k in ("epic_aligned", "component_overlap", "details")):
        raise ValueError("metadata_analysis must contain 'epic_aligned', 'component_overlap', 'details'")
    valid_recs = {"ACCEPT", "DEFER", "CONSIDER", "EVALUATE"}
    if parsed["final_recommendation"] not in valid_recs:
        raise ValueError(f"final_recommendation '{parsed['final_recommendation']}' not in {valid_recs}")
    return parsed


async def _call_gemini(user_message: str) -> dict:
    try:
        import google.generativeai as genai
    except ImportError:
        raise RuntimeError("google-generativeai not installed. Run: pip install google-generativeai")
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=_LLM_SYSTEM_PROMPT,
        generation_config=genai.types.GenerationConfig(temperature=0.1, max_output_tokens=800),
    )
    print("[LLM_ALIGN][Gemini] Sending request…", file=sys.stderr)
    response = model.generate_content(user_message)
    raw = response.text
    print(f"[LLM_ALIGN][Gemini] Response[:300]:\n{raw[:300]}", file=sys.stderr)
    return _parse_llm_json(raw)


async def _call_openai(user_message: str) -> dict:
    try:
        from openai import AsyncOpenAI
    except ImportError:
        raise RuntimeError("openai not installed. Run: pip install openai")
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")
    client = AsyncOpenAI(api_key=api_key)
    print("[LLM_ALIGN][OpenAI] Sending request…", file=sys.stderr)
    completion = await client.chat.completions.create(
        model="gpt-4o-mini", temperature=0.1, max_tokens=800,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": _LLM_SYSTEM_PROMPT},
            {"role": "user",   "content": user_message},
        ],
    )
    raw = completion.choices[0].message.content
    print(f"[LLM_ALIGN][OpenAI] Response[:300]:\n{raw[:300]}", file=sys.stderr)
    return _parse_llm_json(raw)


def _fallback_classical(req: LLMAlignmentRequest, reason: str) -> dict:
    print(f"[LLM_ALIGN] Fallback to classical pipeline ({reason}).", file=sys.stderr)
    result = analyze_sprint_goal_alignment(
        sprint_goal            = req.sprint_goal,
        requirement_title      = req.requirement_title,
        requirement_desc       = req.requirement_description or "",
        requirement_priority   = req.requirement_priority or "Medium",
        requirement_epic       = req.requirement_epic,
        sprint_epic            = req.sprint_epic,
        requirement_components = req.requirement_components,
        sprint_components      = req.sprint_components,
    )
    result["engine"] = "fallback_classical"
    return result


@router.post("/align-sprint-goal", response_model=LLMAlignmentResponse)
async def align_sprint_goal_llm(request: LLMAlignmentRequest):
    """LLM-powered Sprint Goal Alignment (Gemini → OpenAI → classical fallback)."""
    if not request.sprint_goal or not request.requirement_title:
        raise HTTPException(status_code=400, detail="sprint_goal and requirement_title are required")

    user_message   = _build_llm_user_message(request)
    failure_reason = "no LLM API keys configured"

    if os.environ.get("GEMINI_API_KEY", "").strip():
        try:
            parsed = await _call_gemini(user_message)
            parsed["engine"] = "gemini"
            return LLMAlignmentResponse(**parsed)
        except Exception as exc:
            failure_reason = f"Gemini failed: {exc}"
            print(f"[LLM_ALIGN] {failure_reason}", file=sys.stderr)

    if os.environ.get("OPENAI_API_KEY", "").strip():
        try:
            parsed = await _call_openai(user_message)
            parsed["engine"] = "openai"
            return LLMAlignmentResponse(**parsed)
        except Exception as exc:
            failure_reason = f"OpenAI failed: {exc}"
            print(f"[LLM_ALIGN] {failure_reason}", file=sys.stderr)

    fallback = _fallback_classical(request, failure_reason)
    return LLMAlignmentResponse(**fallback)


# ══════════════════════════════════════════════════════════════════════════════
# ST pipeline helper functions  (L1 / L2 / L3 — Layer 4 removed)
# ══════════════════════════════════════════════════════════════════════════════

_ST_BLOCKER_KEYWORDS = {
    "crash", "crashed", "down", "outage", "broken", "not working",
    "emergency", "hotfix", "production issue", "security breach",
    "data loss", "data leak", "payment failure", "site down", "service down",
    "incident", "p0", "sev1", "sev 1",
}

_ST_BLOCKER_PRIORITIES = {"critical", "blocker"}

# Cosine-similarity thresholds (tuned for all-MiniLM-L6-v2)
_ST_HIGHLY_RELEVANT_THRESHOLD = 0.55
_ST_TANGENTIAL_THRESHOLD      = 0.35


def _st_layer1_blocker(title: str, description: str, priority: str) -> tuple[bool, str]:
    """
    Layer 1 – Critical Blocker Detection.
    Returns (is_blocker: bool, reason: str).
    """
    if priority.strip().lower() not in _ST_BLOCKER_PRIORITIES:
        return False, f"Priority '{priority}' is not Critical or Blocker."

    combined = f"{title} {description}".lower()
    found    = [kw for kw in _ST_BLOCKER_KEYWORDS if kw in combined]

    if found:
        reason = f"Production-emergency keywords detected in text with {priority} priority: {', '.join(found)}."
        print(f"[ST_ALIGN][L1] BLOCKER — {reason}", file=sys.stderr)
        return True, reason

    return False, (
        f"Priority is {priority} but no production-emergency keywords found. "
        "Not automatically promoted to blocker."
    )


def _st_layer2_semantic(
    model,
    sprint_goal: str,
    ticket_text: str,
) -> tuple[float, str, str]:
    """
    Layer 2 – Semantic Similarity via all-MiniLM-L6-v2 cosine similarity.
    Returns (score: float, category: str, reasoning: str).
    """
    from sentence_transformers import util as st_util

    embeddings = model.encode([sprint_goal, ticket_text], convert_to_tensor=True)
    cos_score  = float(st_util.cos_sim(embeddings[0], embeddings[1]).item())
    cos_score  = round(max(0.0, min(1.0, cos_score)), 4)

    print(
        f"[ST_ALIGN][L2] cosine={cos_score:.4f}  "
        f"goal='{sprint_goal[:60]}…'  ticket='{ticket_text[:60]}…'",
        file=sys.stderr,
    )

    if cos_score >= _ST_HIGHLY_RELEVANT_THRESHOLD:
        category  = "HIGHLY_RELEVANT"
        reasoning = (
            f"Cosine similarity {cos_score:.2f} ≥ {_ST_HIGHLY_RELEVANT_THRESHOLD} threshold. "
            "The ticket is semantically close to the sprint goal and directly contributes to it."
        )
    elif cos_score >= _ST_TANGENTIAL_THRESHOLD:
        category  = "TANGENTIAL"
        reasoning = (
            f"Cosine similarity {cos_score:.2f} is between {_ST_TANGENTIAL_THRESHOLD} and "
            f"{_ST_HIGHLY_RELEVANT_THRESHOLD}. The ticket shares related themes but does not "
            "directly advance the sprint goal."
        )
    else:
        category  = "UNRELATED"
        reasoning = (
            f"Cosine similarity {cos_score:.2f} < {_ST_TANGENTIAL_THRESHOLD} threshold. "
            "The ticket is semantically distant from the sprint goal."
        )

    print(f"[ST_ALIGN][L2] category={category}", file=sys.stderr)
    return cos_score, category, reasoning


def _st_layer3_metadata(
    ticket_epic: Optional[str],
    sprint_epic: Optional[str],
    ticket_components: Optional[List[str]],
    sprint_components: Optional[List[str]],
) -> tuple[bool, str, List[str], str]:
    """
    Layer 3 – Metadata Traceability (epic string match + component set intersection).
    Returns (epic_aligned, component_overlap_level, matched_components, details).
    """
    t_epic = (ticket_epic or "").strip().lower()
    s_epic = (sprint_epic or "").strip().lower()
    epic_aligned = bool(t_epic and s_epic and t_epic == s_epic)

    t_comps = {c.strip().lower() for c in (ticket_components or []) if c.strip()}
    s_comps = {c.strip().lower() for c in (sprint_components or []) if c.strip()}
    matched = sorted(t_comps & s_comps)

    overlap     = len(matched)
    total_s     = len(s_comps) if s_comps else 1
    ratio       = overlap / total_s

    if ratio >= 0.66:
        level   = "high"
        details = f"Strong component match: {overlap}/{total_s} sprint components covered ({matched})."
    elif ratio >= 0.33:
        level   = "medium"
        details = f"Moderate component match: {overlap}/{total_s} sprint components covered ({matched})."
    elif overlap > 0:
        level   = "low"
        details = f"Weak component match: {overlap}/{total_s} sprint components covered ({matched})."
    else:
        level   = "none"
        details = "No component overlap between ticket and sprint."

    if epic_aligned:
        details += f" Epic '{t_epic}' matches sprint epic."
    else:
        if t_epic and s_epic:
            details += f" Epic mismatch: ticket='{t_epic}' vs sprint='{s_epic}'."
        elif not t_epic:
            details += " Ticket has no epic specified."

    print(f"[ST_ALIGN][L3] epic_aligned={epic_aligned} component_overlap={level}", file=sys.stderr)
    return epic_aligned, level, matched, details


# ══════════════════════════════════════════════════════════════════════════════
# Phase 1 endpoint — Sprint Goal Alignment (alignment state only)
# POST /api/ai/st-align-sprint-goal
# ══════════════════════════════════════════════════════════════════════════════

@router.post("/st-align-sprint-goal", response_model=STAlignmentResponse)
async def st_align_sprint_goal(request: STAlignmentRequest):
    """
    Phase 1 — Sprint Goal Alignment (Sentence-Transformer).

    Uses all-MiniLM-L6-v2 loaded locally at startup — zero latency,
    deterministic, reproducible, no external API calls.

    3-layer pipeline:
      L1  Python keyword string search + priority == Critical/Blocker
      L2  sentence_transformers cosine_similarity  (0.55 / 0.35 thresholds)
      L3  Python set intersection (components) + string == (epic)

    Returns alignment_state + semantic_score_pct ONLY.
    Does NOT return action recommendations — that is Phase 3 POST /decide.
    """
    if not request.sprint_goal or not request.ticket_title:
        raise HTTPException(
            status_code=400,
            detail="sprint_goal and ticket_title are required.",
        )

    model = _get_st_model()
    if model is None:
        raise HTTPException(
            status_code=503,
            detail=(
                f"Sentence-Transformer model '{_st_model_name}' is not available: "
                f"{_st_load_error or 'unknown error'}. "
                "Install with: pip install sentence-transformers"
            ),
        )

    print(
        f"\n[ST_ALIGN] Starting Phase-1 alignment for ticket: '{request.ticket_title}'",
        file=sys.stderr,
    )

    # ── Layer 1 ───────────────────────────────────────────────────────────────
    is_blocker, blocker_reason = _st_layer1_blocker(
        request.ticket_title,
        request.ticket_description or "",
        request.priority,
    )

    # ── Layer 2 ───────────────────────────────────────────────────────────────
    ticket_text = f"{request.ticket_title} {request.ticket_description or ''}".strip()
    semantic_score, category, semantic_reasoning = _st_layer2_semantic(
        model,
        request.sprint_goal,
        ticket_text,
    )

    # ── Layer 3 ───────────────────────────────────────────────────────────────
    epic_aligned, component_overlap, matched_components, metadata_details = _st_layer3_metadata(
        request.ticket_epic,
        request.sprint_epic,
        request.ticket_components,
        request.sprint_components,
    )

    # ── Map L1 + L2 + L3 → Phase 1 alignment_state (NO action verbs) ─────────
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

    print(
        f"[ST_ALIGN] COMPLETE — score={semantic_score:.4f} "
        f"category={category} alignment_state={alignment_state}\n",
        file=sys.stderr,
    )

    return STAlignmentResponse(
        is_critical_blocker = is_blocker,
        blocker_reason       = blocker_reason,
        semantic_score       = semantic_score,
        semantic_score_pct   = int(round(semantic_score * 100)),
        alignment_category   = category,
        semantic_reasoning   = semantic_reasoning,
        epic_aligned         = epic_aligned,
        component_overlap    = component_overlap,
        matched_components   = matched_components,
        metadata_details     = metadata_details,
        alignment_state      = alignment_state,
        alignment_label      = alignment_label,
        model_name           = _st_model_name,
    )


# ══════════════════════════════════════════════════════════════════════════════
# Phase 3 endpoint — Decision Engine
# POST /api/ai/decide
# ══════════════════════════════════════════════════════════════════════════════

@router.post("/decide", response_model=DecisionResponse)
async def decide(request: DecisionRequest):
    """
    Phase 3 — Agile Replanning Decision Engine.

    Combines Phase 1 alignment_state with Phase 2 effort/risk + current sprint
    capacity to produce a single Agile action: ADD | DEFER | SPLIT | SWAP.

    All rules are evaluated in strict priority order (first match wins).
    Fully deterministic — same inputs always produce the same output.

    Rule priority order:
      Rule 1  Emergency / Critical Blocker  (highest priority)
      Rule 2  Scope Creep / High Risk
      Rule 3  Monster Ticket (oversized)
      Rule 4  Urgent Trade-off
      Rule 5  Perfect Fit (default success)
      Rule 6  Catch-all fallback            (lowest priority)
    """
    from decision_engine import calculate_agile_recommendation

    result = calculate_agile_recommendation(
        alignment_state = request.alignment_state,
        effort_sp       = request.effort_sp,
        free_capacity   = request.free_capacity,
        priority        = request.priority,
        risk_level      = request.risk_level,
    )

    print(
        f"[DECIDE] alignment={request.alignment_state} effort={request.effort_sp} "
        f"capacity={request.free_capacity} priority={request.priority} "
        f"risk={request.risk_level} → action={result.action} "
        f"rule='{result.rule_triggered}'",
        file=sys.stderr,
    )

    return DecisionResponse(**result.to_dict())


# ══════════════════════════════════════════════════════════════════════════════
# MODULE 4 ENDPOINT: Simple Sprint Goal Alignment (TF-IDF, no LLM)
# POST /api/ai/align-simple-goal
# ══════════════════════════════════════════════════════════════════════════════

@router.post("/align-simple-goal", response_model=SimpleAlignmentResponse)
async def align_simple_goal(request: SimpleAlignmentRequest):
    """
    MODULE 4: Simple semantic sprint goal alignment using TF-IDF (no LLM required).
    
    Uses tfidf_cosine_similarity() for deterministic, fast alignment scoring.
    Returns alignment_score (0-1) and recommendation level.
    
    Thresholds:
      score >= 0.5  → STRONGLY_ALIGNED (add to sprint)
      score 0.3-0.5 → PARTIALLY_ALIGNED (review with team)
      score < 0.3   → UNALIGNED (likely scope creep)
    """
    if not request.sprint_goal or not request.task_description:
        raise HTTPException(
            status_code=400,
            detail="sprint_goal and task_description are required."
        )
    
    if not is_tfidf_available():
        raise HTTPException(
            status_code=503,
            detail="TF-IDF vectorizer not loaded. Ensure tfidf_registry is initialized."
        )
    
    # Compute cosine similarity between sprint goal and task description
    alignment_score = tfidf_cosine_similarity(request.sprint_goal, request.task_description)
    
    # Handle error case
    if alignment_score < 0:
        raise HTTPException(
            status_code=503,
            detail="TF-IDF similarity computation failed."
        )
    
    # Map score to alignment level
    if alignment_score >= 0.5:
        alignment_level = "STRONGLY_ALIGNED"
        recommendation = (
            f"Task is strongly aligned with sprint goal (score: {alignment_score:.2f}). "
            "Safe to add to sprint."
        )
    elif alignment_score >= 0.3:
        alignment_level = "PARTIALLY_ALIGNED"
        recommendation = (
            f"Task is partially aligned with sprint goal (score: {alignment_score:.2f}). "
            "Review with team before adding."
        )
    else:
        alignment_level = "UNALIGNED"
        recommendation = (
            f"Task is not well aligned with sprint goal (score: {alignment_score:.2f}). "
            "Likely scope creep. Consider deferring or re-scoping."
        )
    
    print(
        f"[SIMPLE_ALIGN] goal='{request.sprint_goal[:50]}...' "
        f"task='{request.task_description[:50]}...' "
        f"score={alignment_score:.4f} level={alignment_level}",
        file=sys.stderr,
    )
    
    return SimpleAlignmentResponse(
        alignment_score=round(alignment_score, 4),
        alignment_level=alignment_level,
        recommendation=recommendation,
    )
