"""
Sprint Goal Alignment Analyzer
─────────────────────────────────────────────────────────────────────────────
Evaluates if a new requirement aligns with the current sprint goal using 
a 4-layer analysis approach:
  1. Critical Blocker Detection
  2. Semantic Similarity Analysis
  3. Metadata Traceability Check
  4. Integrated Recommendation
"""

import re
import sys
from typing import Dict, List, Optional
from collections import Counter
import math


# ─── BLOCKER KEYWORDS ──────────────────────────────────────────────────────
BLOCKER_KEYWORDS = {
    "crash", "down", "outage", "broken", "not working", "emergency",
    "hotfix", "production", "critical", "security breach", "data loss",
    "data leak", "payment failure", "site down", "service down"
}


# ─── LAYER 1: CRITICAL BLOCKER DETECTION ────────────────────────────────
def detect_critical_blocker(requirement_title: str, requirement_desc: str, priority: str) -> tuple:
    """
    Layer 1: Detect if this is a production emergency.
    
    Returns: (is_blocker: bool, reason: str)
    """
    if priority not in ("Critical", "Blocker"):
        return False, "Priority is not Critical/Blocker"
    
    combined_text = f"{requirement_title} {requirement_desc}".lower()
    
    # Check for blocker keywords
    found_keywords = [kw for kw in BLOCKER_KEYWORDS if kw in combined_text]
    
    if found_keywords:
        reason = f"Production emergency detected: {', '.join(found_keywords)}"
        print(f"[CRITICAL BLOCKER DETECTED] {reason}", file=sys.stderr)
        return True, reason
    
    return False, "No production emergency keywords detected"


# ─── LAYER 2: SEMANTIC SIMILARITY ANALYSIS ────────────────────────────────
def tokenize_text(text: str) -> List[str]:
    """Tokenize text for similarity analysis"""
    text = text.lower()
    text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
    return [w for w in text.split() if w]


def calculate_semantic_similarity(goal: str, requirement: str) -> tuple:
    """
    Layer 2: Semantic similarity analysis.
    
    Analyzes the core intent and overlap between sprint goal and requirement.
    
    Returns: (alignment_category, reasoning)
    """
    goal_tokens = set(tokenize_text(goal))
    req_tokens = set(tokenize_text(requirement))
    
    # Calculate Jaccard similarity (intersection / union)
    if not goal_tokens or not req_tokens:
        return "UNRELATED", "Insufficient text for analysis"
    
    intersection = len(goal_tokens & req_tokens)
    union = len(goal_tokens | req_tokens)
    jaccard_similarity = intersection / union if union > 0 else 0
    
    # Calculate overlap percentage
    overlap_pct = (intersection / min(len(goal_tokens), len(req_tokens))) * 100 if min(len(goal_tokens), len(req_tokens)) > 0 else 0
    
    print(f"[SEMANTIC ANALYSIS] Goal tokens: {goal_tokens}", file=sys.stderr)
    print(f"[SEMANTIC ANALYSIS] Req tokens: {req_tokens}", file=sys.stderr)
    print(f"[SEMANTIC ANALYSIS] Jaccard similarity: {jaccard_similarity:.2f}, Overlap: {overlap_pct:.0f}%", file=sys.stderr)
    
    # Categorize alignment
    if jaccard_similarity >= 0.5 or overlap_pct >= 60:
        category = "HIGHLY_RELEVANT"
        reasoning = f"Strong alignment: {overlap_pct:.0f}% token overlap with sprint goal"
    elif jaccard_similarity >= 0.25 or overlap_pct >= 30:
        category = "TANGENTIAL"
        reasoning = f"Related but indirect: {overlap_pct:.0f}% token overlap suggests shared theme"
    else:
        category = "UNRELATED"
        reasoning = f"No significant alignment: only {overlap_pct:.0f}% token overlap"
    
    print(f"[SEMANTIC ANALYSIS] Alignment: {category}", file=sys.stderr)
    return category, reasoning


# ─── LAYER 3: METADATA TRACEABILITY CHECK ────────────────────────────────
def check_metadata_alignment(
    req_epic: str,
    sprint_epic: str,
    req_components: List[str],
    sprint_components: List[str],
) -> tuple:
    """
    Layer 3: Metadata traceability check.
    
    Examines structural relationships (epic alignment, component overlap).
    
    Returns: (epic_aligned: bool, component_overlap: str, details: str)
    """
    req_epic = (req_epic or "").strip().lower()
    sprint_epic = (sprint_epic or "").strip().lower()
    
    # Epic alignment
    epic_aligned = bool(req_epic and sprint_epic and req_epic == sprint_epic)
    
    print(f"[METADATA CHECK] Req epic: '{req_epic}', Sprint epic: '{sprint_epic}'", file=sys.stderr)
    print(f"[METADATA CHECK] Epic aligned: {epic_aligned}", file=sys.stderr)
    
    # Component overlap
    req_comp_set = set([c.lower().strip() for c in (req_components or [])])
    sprint_comp_set = set([c.lower().strip() for c in (sprint_components or [])])
    
    overlap = len(req_comp_set & sprint_comp_set)
    total_sprint_comps = len(sprint_comp_set) if sprint_comp_set else 1
    overlap_ratio = overlap / total_sprint_comps if total_sprint_comps > 0 else 0
    
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
    
    print(f"[METADATA CHECK] Component overlap: {component_overlap}", file=sys.stderr)
    
    return epic_aligned, component_overlap, details


# ─── LAYER 4: INTEGRATED RECOMMENDATION ────────────────────────────────
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
    """
    Layer 4: Integrated recommendation logic.
    
    Combines all 4 layers to produce final recommendation.
    
    Returns: Recommendation dict with final action and reasoning
    """
    
    # Decision logic
    if critical_blocker:
        recommendation = "ACCEPT"
        reason = f"CRITICAL BLOCKER: {blocker_reason}. Production emergency requires immediate attention regardless of sprint goal."
        next_steps = "Accept into current sprint immediately and prioritize above all other work."
    
    elif semantic_category == "HIGHLY_RELEVANT":
        recommendation = "ACCEPT"
        reason = f"DIRECT ALIGNMENT: {semantic_reasoning}. The requirement directly contributes to achieving the sprint goal."
        next_steps = "Accept into current sprint and plan implementation."
    
    elif semantic_category == "TANGENTIAL" and (epic_aligned or component_overlap == "high"):
        recommendation = "CONSIDER"
        reason = f"TANGENTIAL WITH CONTEXT: {semantic_reasoning}. {metadata_details}. The requirement is related to sprint work but does not directly advance the goal. Evaluate capacity before accepting."
        next_steps = "Discuss in next daily standup. Assess team capacity and potential impact on sprint goal before deciding."
    
    elif semantic_category == "TANGENTIAL" and (not epic_aligned and component_overlap in ("low", "none")):
        recommendation = "EVALUATE"
        reason = f"TANGENTIAL UNALIGNED: {semantic_reasoning}. {metadata_details}. The requirement has thematic relation but is structurally disconnected from sprint focus."
        next_steps = "Evaluate carefully in refinement. This may be a distraction — consider deferring unless strategic value is clear."
    
    else:  # UNRELATED
        recommendation = "DEFER"
        reason = f"OUT OF SCOPE: {semantic_reasoning}. The requirement does not align with the sprint goal and should be prioritized for a future sprint."
        next_steps = "Defer to product backlog. Re-prioritize for planning of the next sprint."
    
    print(f"[FINAL RECOMMENDATION] {recommendation}: {reason}", file=sys.stderr)
    
    return {
        "final_recommendation": recommendation,
        "recommendation_reason": reason,
        "next_steps": next_steps,
    }


# ─── MAIN ALIGNMENT ANALYZER ──────────────────────────────────────────────
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
    """
    Main entry point for sprint goal alignment analysis.
    
    Args:
        sprint_goal: Official sprint goal statement
        requirement_title: Title of new requirement
        requirement_desc: Full description of requirement
        requirement_priority: Priority level (Critical/Blocker/High/Medium/Low)
        requirement_epic: Epic name requirement belongs to
        sprint_epic: Primary epic focus of current sprint
        requirement_components: Component tags for requirement (e.g., ["frontend", "auth"])
        sprint_components: Component tags in sprint (e.g., ["frontend", "database"])
    
    Returns:
        Comprehensive analysis dict with all 4 layers + final recommendation
    """
    
    print(f"\n[SPRINT GOAL ALIGNMENT ANALYSIS] Starting for requirement: '{requirement_title}'", file=sys.stderr)
    
    # LAYER 1: Critical Blocker Detection
    is_blocker, blocker_reason = detect_critical_blocker(requirement_title, requirement_desc, requirement_priority)
    
    # LAYER 2: Semantic Similarity Analysis
    req_combined = f"{requirement_title} {requirement_desc}"
    semantic_category, semantic_reasoning = calculate_semantic_similarity(sprint_goal, req_combined)
    
    # LAYER 3: Metadata Traceability Check
    epic_aligned, component_overlap, metadata_details = check_metadata_alignment(
        requirement_epic,
        sprint_epic,
        requirement_components or [],
        sprint_components or [],
    )
    
    # LAYER 4: Integrated Recommendation
    final_rec = generate_recommendation(
        is_blocker,
        blocker_reason,
        semantic_category,
        semantic_reasoning,
        epic_aligned,
        component_overlap,
        metadata_details,
        requirement_priority,
    )
    
    print(f"[SPRINT GOAL ALIGNMENT ANALYSIS] Complete\n", file=sys.stderr)
    
    return {
        "critical_blocker": {
            "detected": is_blocker,
            "reason": blocker_reason,
        },
        "semantic_analysis": {
            "alignment_category": semantic_category,
            "reasoning": semantic_reasoning,
        },
        "metadata_analysis": {
            "epic_aligned": epic_aligned,
            "component_overlap": component_overlap,
            "details": metadata_details,
        },
        "final_recommendation": final_rec["final_recommendation"],
        "recommendation_reason": final_rec["recommendation_reason"],
        "next_steps": final_rec["next_steps"],
    }
