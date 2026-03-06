"""
Input Validation Layer for Agile Requirement Analysis
Detects and rejects gibberish text before it reaches ML models.
"""

import re
from typing import Tuple


def is_gibberish(text: str, min_word_length: int = 3) -> Tuple[bool, str]:
    """
    Detect gibberish/junk text using linguistic heuristics.
    
    Returns:
        (is_gibberish: bool, reason: str)
        - is_gibberish=True means text is junk and should be rejected
        - reason explains why (for user-facing error message)
    
    Heuristics checked:
    1. Text length too short (< 5 chars)
    2. No spaces in long strings (keyboard smash like "asdfghjkl")
    3. Insufficient vowels (% of vowels < threshold)
    4. Too many consecutive consonants (> 5 in a row)
    5. Single character repetition (> 50% of text is same char)
    6. No valid words (words with 3+ chars, common English patterns)
    """
    
    # Clean and normalize
    text = text.strip()
    
    # HEURISTIC 1: Text is too short
    if len(text) < 5:
        return True, "Title/description is too short (minimum 5 characters required)"
    
    # HEURISTIC 2: Long string with no spaces (keyboard smash)
    # If text is > 10 chars but has zero spaces, it's likely gibberish
    if len(text) > 10 and ' ' not in text:
        return True, "Text appears to be keyboard smash (no spaces found). Please use actual words."
    
    # Extract only alphabetic characters for vowel analysis
    alpha_only = re.sub(r'[^a-zA-Z]', '', text)
    
    if not alpha_only:
        return True, "Text must contain at least some letters"
    
    # HEURISTIC 3: Insufficient vowels
    # English text typically has 30-45% vowels
    vowels = len(re.findall(r'[aeiouAEIOU]', alpha_only))
    vowel_ratio = vowels / len(alpha_only) if alpha_only else 0
    
    if vowel_ratio < 0.15:  # Less than 15% vowels = likely gibberish
        return True, f"Text has too few vowels ({vowel_ratio:.0%}). Please check spelling."
    
    # HEURISTIC 4: Too many consecutive consonants
    # English text rarely has > 4 consonants in a row
    consonant_runs = re.findall(r'[bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ]{5,}', alpha_only)
    if consonant_runs:
        longest = max(consonant_runs, key=len)
        return True, f"Text contains too many consecutive consonants: '{longest}'. Please use real words."
    
    # HEURISTIC 5: Character repetition (same char > 50%)
    if alpha_only:
        char_counts = {}
        for char in alpha_only.lower():
            char_counts[char] = char_counts.get(char, 0) + 1
        
        max_count = max(char_counts.values())
        repetition_ratio = max_count / len(alpha_only)
        
        if repetition_ratio > 0.5:  # Same character > 50% of text
            most_common = max(char_counts, key=char_counts.get)
            return True, f"Text is mostly the character '{most_common}' repeated. Please provide meaningful content."
    
    # HEURISTIC 6: No valid English words
    # Split by non-alphanumeric and check if any word has 3+ chars (likely real word)
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    real_words = [w for w in words if len(w) >= min_word_length]
    
    if not real_words:
        return True, f"Text must contain at least one meaningful word (3+ characters). Example: 'Add login feature'"
    
    # Text appears to be valid
    return False, ""


def validate_requirement(title: str, description: str = "") -> Tuple[bool, str]:
    """
    Validate both title and description for an Agile requirement.
    
    Returns:
        (is_valid: bool, error_message: str)
        - is_valid=True means both title and description are acceptable
        - error_message contains the rejection reason if invalid
    """
    
    # Validate title (required)
    is_gibberish_title, reason_title = is_gibberish(title, min_word_length=3)
    if is_gibberish_title:
        return False, f"Title is invalid: {reason_title}"
    
    # Validate description (optional, but if provided, must be valid)
    if description and description.strip():
        is_gibberish_desc, reason_desc = is_gibberish(description, min_word_length=2)
        if is_gibberish_desc:
            return False, f"Description is invalid: {reason_desc}"
    
    return True, ""
