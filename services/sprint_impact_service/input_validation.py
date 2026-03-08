"""
Input Validation Layer for Agile Requirement Analysis
Detects and rejects gibberish text before it reaches ML models.
"""

import re
from typing import Tuple


def is_gibberish(text: str, min_word_length: int = 3) -> Tuple[bool, str]:
    """
    Detect gibberish/junk text using linguistic heuristics.
    """
    if not text:
        return True, "Text cannot be empty."

    # Clean and normalize
    text = text.strip()
    
    # HEURISTIC 1: Text is too short
    if len(text) < 5:
        return True, "Title/description is too short (minimum 5 characters required)"
    
    # HEURISTIC 2: Long string with no spaces (keyboard smash)
    if len(text) > 15 and ' ' not in text:
        return True, "Text appears to be keyboard smash (no spaces found). Please use actual words."
    
    # Extract only alphabetic characters for vowel/repetition analysis
    alpha_only = re.sub(r'[^a-zA-Z]', '', text)
    
    if not alpha_only:
        return True, "Text must contain at least some letters"
    
    # HEURISTIC 3: Insufficient vowels
    vowels = len(re.findall(r'[aeiouAEIOU]', alpha_only))
    vowel_ratio = vowels / len(alpha_only) if alpha_only else 0
    
    if len(alpha_only) > 10 and vowel_ratio < 0.15:  
        return True, f"Text has too few vowels ({vowel_ratio:.0%}). Please check spelling."
    
    # HEURISTIC 4: Too many consecutive consonants
    # We check the ORIGINAL text here so spaces break the consonant chains.
    # We use 7 because words like "catchphrase" have 6. 'y' is excluded as it often acts as a vowel (e.g., "rhythm").
    consonant_runs = re.findall(r'[bcdfghjklmnpqrstvwxzBCDFGHJKLMNPQRSTVWXZ]{7,}', text)
    if consonant_runs:
        longest = max(consonant_runs, key=len)
        return True, f"Text contains too many consecutive consonants: '{longest}'. Please use real words."
    
    # HEURISTIC 5: Character repetition (same char > 50%)
    if len(alpha_only) > 10:
        char_counts = {}
        for char in alpha_only.lower():
            char_counts[char] = char_counts.get(char, 0) + 1
        
        max_count = max(char_counts.values())
        repetition_ratio = max_count / len(alpha_only)
        
        if repetition_ratio > 0.5:  
            most_common = max(char_counts, key=char_counts.get)
            return True, f"Text is mostly the character '{most_common}' repeated. Please provide meaningful content."
    
    # HEURISTIC 6: No valid English words
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    real_words = [w for w in words if len(w) >= min_word_length]
    
    if not real_words and len(alpha_only) > 0:
        return True, f"Text must contain at least one meaningful word (3+ characters)."
    
    # Text appears to be valid
    return False, ""


def validate_requirement(title: str, description: str = "") -> Tuple[bool, str]:
    """
    Validate both title and description for an Agile requirement.
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