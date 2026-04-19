"""
Input Validation Layer for Agile Requirement Analysis
Detects and rejects gibberish text while permitting technical jargon.
"""

import re
from typing import Tuple

def is_gibberish(text: str, min_word_length: int = 3) -> Tuple[bool, str]:
    """
    Detect gibberish/junk text using software-engineering-aware heuristics.
    """
    if not text:
        return True, "Text cannot be empty."

    # Clean and normalize
    text = text.strip()
    
    # HEURISTIC 1: Text is too short
    if len(text) < 5:
        return True, "Title/description is too short (minimum 5 characters required)"
    
    # HEURISTIC 2: Long string with no spaces (keyboard smash)
    # Permitting common technical paths/strings if they contain slashes or dots
    if len(text) > 25 and ' ' not in text and '/' not in text and '.' not in text:
        return True, "Text appears to be keyboard smash (no spaces found)."
    
    # --- TECHNICAL REFINEMENT ---
    # Identify CamelCase (e.g., XGBClassifier) or strings with numbers (e.g., OAuth2)
    # We temporarily remove these from the linguistic check so they don't trigger false positives.
    tech_pattern = r'\b(?:[A-Z]+[a-z]+[A-Z][a-z\w]*|[A-Z]{2,}\d*|\w+\d+\w*)\b'
    natural_language_only = re.sub(tech_pattern, '', text)
    
    # Extract only alphabetic characters for vowel/repetition analysis
    alpha_only = re.sub(r'[^a-zA-Z]', '', natural_language_only)
    
    # If the text was ONLY technical terms (e.g., "PostgreSQL OAuth2"), it is valid.
    if not alpha_only and len(re.findall(tech_pattern, text)) > 0:
        return False, ""
    
    if not alpha_only and not re.findall(tech_pattern, text):
        return True, "Text must contain at least some letters or valid technical terms"
    
    # HEURISTIC 3: Insufficient vowels
    # Threshold reduced to 10% to accommodate technical abbreviations (src, docs, config)
    vowels = len(re.findall(r'[aeiouAEIOU]', alpha_only))
    vowel_ratio = vowels / len(alpha_only) if alpha_only else 0
    
    if len(alpha_only) > 12 and vowel_ratio < 0.10:  
        return True, f"Text has too few vowels ({vowel_ratio:.0%}). Please check spelling."
    
    # HEURISTIC 4: Too many consecutive consonants
    # Threshold increased to 10 to permit strings like "XMLHttpRequest" or "PostgreSQL" 
    # if they weren't caught by the tech_pattern.
    consonant_runs = re.findall(r'[bcdfghjklmnpqrstvwxzBCDFGHJKLMNPQRSTVWXZ]{10,}', text)
    if consonant_runs:
        longest = max(consonant_runs, key=len)
        return True, f"Text contains too many consecutive consonants: '{longest}'."
    
    # HEURISTIC 5: Character repetition (same char > 50%)
    if len(alpha_only) > 10:
        char_counts = {}
        for char in alpha_only.lower():
            char_counts[char] = char_counts.get(char, 0) + 1
        
        max_count = max(char_counts.values())
        repetition_ratio = max_count / len(alpha_only)
        
        if repetition_ratio > 0.5:  
            most_common = max(char_counts, key=char_counts.get)
            return True, f"Text is mostly the character '{most_common}' repeated."
    
    # HEURISTIC 6: No valid English words
    # Check for words in natural language OR the presence of valid tech terms
    words = re.findall(r'\b[a-zA-Z]+\b', natural_language_only.lower())
    real_words = [w for w in words if len(w) >= min_word_length]
    tech_words = re.findall(tech_pattern, text)
    
    if not real_words and not tech_words:
        return True, "Text must contain at least one meaningful word or technical term."
    
    return False, ""


def validate_requirement(title: str, description: str = "") -> Tuple[bool, str]:
    """
    Validate both title and description for an Agile requirement.
    """
    is_gibberish_title, reason_title = is_gibberish(title, min_word_length=3)
    if is_gibberish_title:
        return False, f"Title is invalid: {reason_title}"
    
    if description and description.strip():
        is_gibberish_desc, reason_desc = is_gibberish(description, min_word_length=2)
        if is_gibberish_desc:
            return False, f"Description is invalid: {reason_desc}"
    
    return True, ""