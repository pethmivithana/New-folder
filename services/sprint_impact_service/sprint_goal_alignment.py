"""
Sprint Goal Alignment Analyzer
─────────────────────────────────────────────────────────────────────────────
Evaluates if a new requirement aligns with the current sprint goal using
a 4-layer analysis approach:
  1. Critical Blocker Detection
  2. Semantic Similarity Analysis  ← now uses TF-IDF cosine similarity
  3. Metadata Traceability Check
  4. Integrated Recommendation

TF-IDF is used in Layer 2 when the standalone tfidf_vectorizer.pkl is loaded.
Falls back to Jaccard similarity when TF-IDF is unavailable.
"""

import re
import sys
from typing import Dict, List, Optional
import math

from tfidf_registry import tfidf_cosine_similarity, is_tfidf_available

# ─── BLOCKER KEYWORDS ────────────────────────────────────────────────────────
BLOCKER_KEYWORDS = {
    "crash", "down", "outage", "broken", "not working", "emergency",
    "hotfix", "production", "critical", "security breach", "data loss",
    "data leak", "payment failure", "site down", "service down"
}


# ─── LAYER 1: CRITICAL BLOCKER DETECTION ─────────────────────────────────────
def detect_critical_blocker(requirement_title: str, requirement_desc: str, priority: str) -> tuple:
    if priority not in ("Critical", "Blocker"):
        return False, "Priority is not Critical/Blocker"

    combined_text = f"{requirement_title} {requirement_desc}".lower()
    found_keywords = [kw for kw in BLOCKER_KEYWORDS if kw in combined_text]

    if found_keywords:
        reason = f"Production emergency detected: {', '.join(found_keywords)}"
        print(f"[CRITICAL BLOCKER DETECTED] {reason}", file=sys.stderr)
        return True, reason

    return False, "No production emergency keywords detected"


# ─── LAYER 2: SEMANTIC SIMILARITY ANALYSIS ───────────────────────────────────

def tokenize_text(text: str) -> List[str]:
    text = text.lower()
    text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
    return [w for w in text.split() if w]


def _jaccard_similarity(goal: str, requirement: str) -> tuple:
    """Pure token-overlap Jaccard similarity (fallback when TF-IDF unavailable)."""
    goal_tokens = set(tokenize_text(goal))
    req_tokens  = set(tokenize_text(requirement))

    if not goal_tokens or not req_tokens:
        return 0.0, 0.0

    intersection = len(goal_tokens & req_tokens)
    union        = len(goal_tokens | req_tokens)
    jaccard      = intersection / union if union > 0 else 0.0
    overlap_pct  = (intersection / min(len(goal_tokens), len(req_tokens))) * 100 \
                   if min(len(goal_tokens), len(req_tokens)) > 0 else 0.0
    return jaccard, overlap_pct


def calculate_semantic_similarity(goal: str, requirement: str) -> tuple:
    """
    Layer 2: Semantic similarity analysis.

    When tfidf_vectorizer.pkl is loaded:
      - Uses cosine similarity between TF-IDF vectors of goal and requirement.
      - Cosine similarity in [0, 1] is mapped to the same category thresholds
        as the Jaccard overlap_pct (>= 0.50 → HIGHLY_RELEVANT, >= 0.25 → TANGENTIAL).

    Fallback (TF-IDF not available):
      - Jaccard overlap (token intersection / union).

    Returns: (alignment_category, reasoning, similarity_score)
    """
    if is_tfidf_available():
        cosine = tfidf_cosine_similarity(goal, requirement)

        if cosine < 0:
            # Vectorizer returned error, fall back to Jaccard
            jaccard, overlap_pct = _jaccard_similarity(goal, requirement)
            cosine = jaccard
            method = "Jaccard (TF-IDF error)"
        else:
            method = "TF-IDF cosine"

        score = cosine  # in [0, 1]

        print(
            f"[SEMANTIC ANALYSIS][{method}] goal='{goal[:60]}' "
            f"req='{requirement[:60]}' similarity={score:.3f}",
            file=sys.stderr,
        )

        if score >= 0.50:
            category  = "HIGHLY_RELEVANT"
            reasoning = (
                f"Strong alignment ({method} similarity {score:.2f}): "
                "requirement shares substantial semantic content with sprint goal"
            )
        elif score >= 0.25:
            category  = "TANGENTIAL"
            reasoning = (
                f"Related but indirect ({method} similarity {score:.2f}): "
                "requirement shares some semantic content with sprint goal"
            )
        else:
            category  = "UNRELATED"
            reasoning = (
                f"No significant alignment ({method} similarity {score:.2f}): "
                "requirement does not semantically match sprint goal"
            )

        print(f"[SEMANTIC ANALYSIS] Alignment: {category}", file=sys.stderr)
        return category, reasoning

    # ── Fallback: Jaccard ─────────────────────────────────────────────────────
    jaccard, overlap_pct = _jaccard_similarity(goal, requirement)

    print(
        f"[SEMANTIC ANALYSIS][Jaccard fallback] "
        f"jaccard={jaccard:.3f} overlap={overlap_pct:.0f}%",
        file=sys.stderr,
    )

    if jaccard >= 0.50 or overlap_pct >= 60:
        category  = "HIGHLY_RELEVANT"
        reasoning = f"Strong alignment: {overlap_pct:.0f}% token overlap with sprint goal"
    elif jaccard >= 0.25 or overlap_pct >= 30:
        category  = "TANGENTIAL"
        reasoning = f"Related but indirect: {overlap_pct:.0f}% token overlap suggests shared theme"
    else:
        category  = "UNRELATED"
        reasoning = f"No significant alignment: only {overlap_pct:.0f}% token overlap"

    print(f"[SEMANTIC ANALYSIS] Alignment: {category}", file=sys.stderr)
    return category, reasoning


# ─── LAYER 3: METADATA TRACEABILITY CHECK ────────────────────────────────────
def check_metadata_alignment(
    req_epic: str,
    sprint_epic: str,
    req_components: List[str],
    sprint_components: List[str],
) -> tuple:
    req_epic    = (req_epic    or "").strip().lower()
    sprint_epic = (sprint_epic or "").strip().lower()

    epic_aligned = bool(req_epic and sprint_epic and req_epic == sprint_epic)

    print(f"[METADATA CHECK] Req epic: '{req_epic}', Sprint epic: '{sprint_epic}'", file=sys.stderr)
    print(f"[METADATA CHECK] Epic aligned: {epic_aligned}", file=sys.stderr)

    req_comp_set    = set(c.lower().strip() for c in (req_components or []))
    sprint_comp_set = set(c.lower().strip() for c in (sprint_components or []))

    overlap              = len(req_comp_set & sprint_comp_set)
    total_sprint_comps   = len(sprint_comp_set) if sprint_comp_set else 1
    overlap_ratio        = overlap / total_sprint_comps if total_sprint_comps > 0 else 0

    print(f"[METADATA CHECK] Component overlap: {overlap}/{total_sprint_comps}", file=sys.stderr)

    if overlap_ratio >= 0.66:
        component_overlap = "high"
        details = f"Strong component alignment: {overlap}/{total_sprint_comps} components match"
    elif overlap_ratio >= 0.33:
        component_overlap = "medium"
        details = f"Moderate component alignment: {overlap}/{total_sprint_comps} components match"
    elif overlap > 0:
        component_overlap = "low"
        details = f"Weak component alignment: {overlap}/{total_sprint_comps} components match"
    else:
        component_overlap = "none"
        details = "No component alignment"

    return epic_aligned, component_overlap, details


# ─── LAYER 4: INTEGRATED RECOMMENDATION ──────────────────────────────────────
def generate_recommendation(
    critical_blocker: bool,
    blocker_reason: str,
    semantic_category: str,
    semantic_reasoning: str,
    epic_aligned: bool,
    component_overlap: str,
    metadata_details: str,
    req_priority: str,
) -> Dict:
    if critical_blocker:
        recommendation = "ACCEPT"
        reason = (
            f"CRITICAL BLOCKER: {blocker_reason}. "
            "Production emergency requires immediate attention regardless of sprint goal."
        )
        next_steps = "Accept into current sprint immediately and prioritize above all other work."

    elif semantic_category == "HIGHLY_RELEVANT":
        recommendation = "ACCEPT"
        reason = (
            f"DIRECT ALIGNMENT: {semantic_reasoning}. "
            "The requirement directly contributes to achieving the sprint goal."
        )
        next_steps = "Accept into current sprint and plan implementation."

    elif semantic_category == "TANGENTIAL" and (epic_aligned or component_overlap == "high"):
        recommendation = "CONSIDER"
        reason = (
            f"TANGENTIAL WITH CONTEXT: {semantic_reasoning}. {metadata_details}. "
            "The requirement is related to sprint work but does not directly advance the goal. "
            "Evaluate capacity before accepting."
        )
        next_steps = (
            "Discuss in next daily standup. "
            "Assess team capacity and potential impact on sprint goal before deciding."
        )

    elif semantic_category == "TANGENTIAL" and (not epic_aligned and component_overlap in ("low", "none")):
        recommendation = "EVALUATE"
        reason = (
            f"TANGENTIAL UNALIGNED: {semantic_reasoning}. {metadata_details}. "
            "The requirement has thematic relation but is structurally disconnected from sprint focus."
        )
        next_steps = (
            "Evaluate carefully in refinement. "
            "This may be a distraction — consider deferring unless strategic value is clear."
        )

    else:
        recommendation = "DEFER"
        reason = (
            f"OUT OF SCOPE: {semantic_reasoning}. "
            "The requirement does not align with the sprint goal and should be prioritized for a future sprint."
        )
        next_steps = "Defer to product backlog. Re-prioritize for planning of the next sprint."

    print(f"[FINAL RECOMMENDATION] {recommendation}: {reason}", file=sys.stderr)

    return {
        "final_recommendation":  recommendation,
        "recommendation_reason": reason,
        "next_steps":            next_steps,
    }


# ─── MAIN ALIGNMENT ANALYZER ─────────────────────────────────────────────────
def analyze_sprint_goal_alignment(
    sprint_goal: str,
    requirement_title: str,
    requirement_desc: str,
    requirement_priority: str,
    requirement_epic: Optional[str] = None,
    sprint_epic: Optional[str] = None,
    requirement_components: Optional[List[str]] = None,
    sprint_components: Optional[List[str]] = None,
) -> Dict:
    print(
        f"\n[SPRINT GOAL ALIGNMENT ANALYSIS] Starting for requirement: '{requirement_title}' "
        f"(TF-IDF: {'available' if is_tfidf_available() else 'unavailable — Jaccard fallback'})",
        file=sys.stderr,
    )

    is_blocker, blocker_reason = detect_critical_blocker(
        requirement_title, requirement_desc, requirement_priority
    )

    req_combined = f"{requirement_title} {requirement_desc}"
    semantic_category, semantic_reasoning = calculate_semantic_similarity(
        sprint_goal, req_combined
    )

    epic_aligned, component_overlap, metadata_details = check_metadata_alignment(
        requirement_epic,
        sprint_epic,
        requirement_components or [],
        sprint_components or [],
    )

    final_rec = generate_recommendation(
        is_blocker, blocker_reason,
        semantic_category, semantic_reasoning,
        epic_aligned, component_overlap, metadata_details,
        requirement_priority,
    )

    print(f"[SPRINT GOAL ALIGNMENT ANALYSIS] Complete\n", file=sys.stderr)

    return {
        "critical_blocker": {
            "detected": is_blocker,
            "reason":   blocker_reason,
        },
        "semantic_analysis": {
            "alignment_category": semantic_category,
            "reasoning":          semantic_reasoning,
        },
        "metadata_analysis": {
            "epic_aligned":      epic_aligned,
            "component_overlap": component_overlap,
            "details":           metadata_details,
        },
        "final_recommendation":  final_rec["final_recommendation"],
        "recommendation_reason": final_rec["recommendation_reason"],
        "next_steps":            final_rec["next_steps"],
    }