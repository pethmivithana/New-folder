"""
Story Point Suggestion Engine

Uses ML-inspired similarity matching and fibonacci constraint validation.
Fibonacci numbers: 1, 2, 3, 5, 8, 13, 21

Suggests SP based on:
1. Historical backlog items with similar titles/descriptions
2. Keyword complexity heuristics
3. Enforces fibonacci constraint for all suggestions
"""

from database import get_database
from typing import List, Dict, Optional
import math


FIBONACCI_SEQUENCE = [1, 2, 3, 5, 8, 13, 21]


def is_valid_fibonacci(sp: int) -> bool:
    """Check if story points value is a valid Fibonacci number."""
    return sp in FIBONACCI_SEQUENCE


def get_nearest_fibonacci(sp: int) -> int:
    """Find nearest Fibonacci number to given story points."""
    if is_valid_fibonacci(sp):
        return sp
    
    # Find closest Fibonacci number
    closest = FIBONACCI_SEQUENCE[0]
    for fib in FIBONACCI_SEQUENCE:
        if abs(fib - sp) < abs(closest - sp):
            closest = fib
    return closest


def calculate_title_complexity(title: str) -> float:
    """
    Estimate complexity from title keywords.
    
    Returns a score from 0.0 to 1.0:
      - 0.0-0.3: Simple tasks (add, create, fix, update single item)
      - 0.3-0.6: Moderate (refactor, integrate, implement)
      - 0.6-1.0: Complex (redesign, rewrite, overhaul, platform-wide)
    """
    title_lower = title.lower()
    
    simple_keywords = ["add", "create", "fix", "update", "simple", "basic"]
    moderate_keywords = ["refactor", "improve", "integrate", "implement", "enhance"]
    complex_keywords = ["redesign", "rewrite", "overhaul", "migrate", "rebuild", "restructure"]
    
    simple_score = sum(1 for kw in simple_keywords if kw in title_lower)
    moderate_score = sum(2 for kw in moderate_keywords if kw in title_lower)
    complex_score = sum(3 for kw in complex_keywords if kw in title_lower)
    
    total_score = simple_score + moderate_score + complex_score
    word_count = len(title.split())
    
    # Longer titles = more complex
    length_factor = min(1.0, word_count / 10.0) * 0.3
    
    # Keyword-based factor
    keyword_factor = min(1.0, total_score / 5.0) * 0.7
    
    return keyword_factor + length_factor


def calculate_description_complexity(description: str) -> float:
    """
    Estimate complexity from description length and keywords.
    
    Longer descriptions with more dependencies = higher complexity.
    """
    if not description:
        return 0.0
    
    desc_lower = description.lower()
    word_count = len(description.split())
    
    # Length factor (more words = potentially more complex)
    length_factor = min(1.0, word_count / 100.0) * 0.5
    
    # Dependency keywords
    dependency_keywords = [
        "depends on", "requires", "needs", "integrate with", 
        "coordinate with", "backend", "frontend", "database",
        "api", "third party", "external", "multiple teams"
    ]
    dependency_score = sum(1 for kw in dependency_keywords if kw in desc_lower)
    
    # Complexity keywords
    complexity_keywords = [
        "complex", "difficult", "tricky", "edge case", "unknown",
        "research", "investigate", "prototype", "poc"
    ]
    complexity_score = sum(1 for kw in complexity_keywords if kw in desc_lower)
    
    dependency_factor = min(1.0, dependency_score / 3.0) * 0.3
    complexity_factor = min(1.0, complexity_score / 2.0) * 0.2
    
    return length_factor + dependency_factor + complexity_factor


def tokenize_text(text: str) -> List[str]:
    """Simple tokenization: split on whitespace and punctuation."""
    import re
    text = text.lower()
    # Remove special characters and split
    tokens = re.findall(r'\b\w+\b', text)
    return tokens


def calculate_cosine_similarity(tokens1: List[str], tokens2: List[str]) -> float:
    """
    Calculate cosine similarity between two token sets.
    Returns value between 0.0 and 1.0.
    """
    if not tokens1 or not tokens2:
        return 0.0
    
    # Build vectors
    all_tokens = set(tokens1 + tokens2)
    vec1 = [1.0 if t in tokens1 else 0.0 for t in all_tokens]
    vec2 = [1.0 if t in tokens2 else 0.0 for t in all_tokens]
    
    # Dot product
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    
    # Magnitudes
    mag1 = math.sqrt(sum(a * a for a in vec1))
    mag2 = math.sqrt(sum(b * b for b in vec2))
    
    if mag1 == 0 or mag2 == 0:
        return 0.0
    
    return dot_product / (mag1 * mag2)


async def suggest_story_points(
    space_id: str, 
    requirement_title: str, 
    requirement_description: str = ""
) -> Dict:
    """
    Suggest story points for a new requirement using:
    1. Historical similarity (find similar items from completed work)
    2. Complexity heuristics (title + description analysis)
    
    Returns:
      {
        "suggested_sp": 5,  # Fibonacci number
        "confidence": 0.75,  # 0.0-1.0 confidence score
        "reasoning": "Similar to X (8 SP), but simpler (~60% complexity)",
        "historical_match": {...}  or None if no match
      }
    """
    db = get_database()
    
    # Tokenize requirement
    req_tokens = tokenize_text(f"{requirement_title} {requirement_description}")
    title_complexity = calculate_title_complexity(requirement_title)
    desc_complexity = calculate_description_complexity(requirement_description)
    
    # Overall complexity score (0.0-1.0)
    overall_complexity = (title_complexity + desc_complexity) / 2.0
    
    # Find similar historical items from this space's backlog
    all_items = []
    async for item in db.backlog_items.find({"space_id": space_id}):
        all_items.append(item)
    
    if not all_items:
        # No historical data: estimate from complexity alone
        sp_estimate = _estimate_sp_from_complexity(overall_complexity)
        suggested_sp = get_nearest_fibonacci(sp_estimate)
        
        return {
            "suggested_sp": suggested_sp,
            "confidence": 0.5,
            "reasoning": f"No historical data available. Based on complexity estimate ({overall_complexity:.1%}), suggested {suggested_sp} SP.",
            "historical_match": None,
        }
    
    # Find most similar historical item
    best_match = None
    best_similarity = 0.0
    
    for item in all_items:
        item_tokens = tokenize_text(f"{item.get('title', '')} {item.get('description', '')}")
        similarity = calculate_cosine_similarity(req_tokens, item_tokens)
        
        if similarity > best_similarity:
            best_similarity = similarity
            best_match = item
    
    # If we found a similar item, use it as baseline
    if best_match and best_similarity > 0.3:  # Threshold: 30% similarity
        historical_sp = best_match.get("story_points", 5)
        historical_complexity = (
            calculate_title_complexity(best_match.get("title", "")) +
            calculate_description_complexity(best_match.get("description", ""))
        ) / 2.0
        
        # Adjust historical SP based on complexity difference
        complexity_ratio = overall_complexity / max(historical_complexity, 0.1)
        adjusted_sp = int(historical_sp * complexity_ratio)
        suggested_sp = get_nearest_fibonacci(adjusted_sp)
        
        confidence = min(0.85, 0.5 + (best_similarity * 0.35))  # Cap at 85%
        reasoning = f"Similar to '{best_match.get('title')}' ({historical_sp} SP, {best_similarity:.0%} match). Adjusted to {suggested_sp} SP based on complexity ({overall_complexity:.0%})."
        
        return {
            "suggested_sp": suggested_sp,
            "confidence": round(confidence, 2),
            "reasoning": reasoning,
            "historical_match": {
                "title": best_match.get("title"),
                "story_points": historical_sp,
                "similarity": round(best_similarity, 2),
            },
        }
    
    # No good historical match: use complexity heuristic
    sp_estimate = _estimate_sp_from_complexity(overall_complexity)
    suggested_sp = get_nearest_fibonacci(sp_estimate)
    confidence = min(0.6, 0.2 + (overall_complexity * 0.4))
    
    return {
        "suggested_sp": suggested_sp,
        "confidence": round(confidence, 2),
        "reasoning": f"Based on complexity analysis ({overall_complexity:.0%}), suggested {suggested_sp} SP. (No similar historical items found)",
        "historical_match": None,
    }


def _estimate_sp_from_complexity(complexity: float) -> int:
    """
    Map complexity score (0.0-1.0) to story point estimate.
    
    - 0.0-0.2:   1 SP (trivial)
    - 0.2-0.35:  2 SP (very simple)
    - 0.35-0.5:  3 SP (simple)
    - 0.5-0.65:  5 SP (moderate)
    - 0.65-0.8:  8 SP (complex)
    - 0.8-0.95: 13 SP (very complex)
    - 0.95-1.0: 21 SP (extremely complex)
    """
    if complexity < 0.2:
        return 1
    elif complexity < 0.35:
        return 2
    elif complexity < 0.5:
        return 3
    elif complexity < 0.65:
        return 5
    elif complexity < 0.8:
        return 8
    elif complexity < 0.95:
        return 13
    else:
        return 21
