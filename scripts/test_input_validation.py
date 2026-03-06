"""
Test script to demonstrate input validation in action.
Run this to see how various inputs are handled.
"""

import sys
sys.path.insert(0, '/vercel/share/v0-project/services/sprint_impact_service')

from input_validation import is_gibberish, validate_requirement


def test_case(title: str, text: str, expected_gibberish: bool):
    """Test a single input and display results."""
    is_gibberish_result, reason = is_gibberish(text)
    status = "✓ REJECTED" if is_gibberish_result else "✓ ACCEPTED"
    
    print(f"\n{'='*80}")
    print(f"TEST: {title}")
    print(f"{'='*80}")
    print(f"Input: {text!r}")
    print(f"Result: {status}")
    if is_gibberish_result:
        print(f"Reason: {reason}")
    
    # Verify expectation
    if is_gibberish_result == expected_gibberish:
        print(f"✓ PASSED (expected {'REJECTED' if expected_gibberish else 'ACCEPTED'})")
    else:
        print(f"✗ FAILED (expected {'REJECTED' if expected_gibberish else 'ACCEPTED'})")


print("\n" + "="*80)
print("INPUT VALIDATION TEST SUITE")
print("="*80)

# ─────────────────────────────────────────────────────────────────────────────
# GIBBERISH CASES (should be rejected)
# ─────────────────────────────────────────────────────────────────────────────
print("\n[GIBBERISH INPUTS - should all be REJECTED]\n")

test_case(
    "Keyboard smash (no spaces)",
    "asdfghjklqwerty",
    expected_gibberish=True
)

test_case(
    "All consonants (no vowels)",
    "bbbcccdddfff",
    expected_gibberish=True
)

test_case(
    "Repeated character",
    "aaaaaaaaaa",
    expected_gibberish=True
)

test_case(
    "Too many consonants in a row",
    "strmnplbrgth test",
    expected_gibberish=True
)

test_case(
    "Too short",
    "abc",
    expected_gibberish=True
)

test_case(
    "Numbers only",
    "12345",
    expected_gibberish=True
)

test_case(
    "Mixed gibberish with spaces",
    "xyzqwe qwerty asdfgh",
    expected_gibberish=True
)

# ─────────────────────────────────────────────────────────────────────────────
# VALID CASES (should be accepted)
# ─────────────────────────────────────────────────────────────────────────────
print("\n\n[VALID INPUTS - should all be ACCEPTED]\n")

test_case(
    "Real Agile requirement",
    "Add user authentication feature",
    expected_gibberish=False
)

test_case(
    "Short but valid",
    "Fix login bug",
    expected_gibberish=False
)

test_case(
    "Longer description",
    "Implement database indexing to improve query performance on large datasets",
    expected_gibberish=False
)

test_case(
    "With technical terms",
    "Refactor API endpoints for scalability",
    expected_gibberish=False
)

test_case(
    "With numbers and hyphens",
    "Setup CI-CD pipeline for automated testing",
    expected_gibberish=False
)

test_case(
    "Minimum valid length",
    "Improve",
    expected_gibberish=False
)

# ─────────────────────────────────────────────────────────────────────────────
# EDGE CASES
# ─────────────────────────────────────────────────────────────────────────────
print("\n\n[EDGE CASES]\n")

test_case(
    "Single word (valid)",
    "Refactoring",
    expected_gibberish=False
)

test_case(
    "With special characters",
    "Add OAuth 2.0 authentication!",
    expected_gibberish=False
)

test_case(
    "CamelCase (valid)",
    "ImplementUserAuthentication",
    expected_gibberish=False
)

# ─────────────────────────────────────────────────────────────────────────────
# FULL REQUIREMENT VALIDATION
# ─────────────────────────────────────────────────────────────────────────────
print("\n\n" + "="*80)
print("FULL REQUIREMENT VALIDATION (title + description)")
print("="*80)

test_cases = [
    ("Valid requirement", "Add login feature", "Implement secure user authentication with JWT tokens", True),
    ("Gibberish title", "asdfghjkl", "Some description", False),
    ("Gibberish description", "Add feature", "qwerty asdfgh zxcvbn", False),
    ("Both valid", "Setup database", "Create MongoDB collections with proper indexing", True),
    ("Empty description (OK)", "Add feature", "", True),
    ("Both gibberish", "asdfgh", "qwerty", False),
]

for test_name, title, description, should_be_valid in test_cases:
    is_valid, error_msg = validate_requirement(title, description)
    status = "✓ ACCEPTED" if is_valid else "✗ REJECTED"
    
    print(f"\n{'-'*80}")
    print(f"TEST: {test_name}")
    print(f"{'-'*80}")
    print(f"Title: {title!r}")
    print(f"Description: {description!r}")
    print(f"Result: {status}")
    if error_msg:
        print(f"Message: {error_msg}")
    
    if is_valid == should_be_valid:
        print(f"✓ PASSED")
    else:
        print(f"✗ FAILED (expected {'ACCEPTED' if should_be_valid else 'REJECTED'})")


print("\n" + "="*80)
print("TEST SUITE COMPLETE")
print("="*80 + "\n")
