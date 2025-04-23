"""
Spell correction utility for P.U.L.S.E. (Prime Uminda's Learning System Engine)

This module provides basic spell correction functionality to handle typos in user input.
"""

import re
from typing import Tuple, Optional

# Common typos and their corrections
COMMON_TYPOS = {
    # Greetings
    "hi": ["hi", "hey", "hello", "helo", "hallo", "hola", "hy", "hii", "hiii"],
    "hey": ["hey", "hay", "hye", "heya", "heyy", "heyya"],
    "hello": ["hello", "helo", "hallo", "hullo", "hallo", "helo"],

    # Common words
    "thanks": ["thanks", "thanx", "thnx", "thnks", "thx", "thankyou", "thank you"],
    "please": ["please", "plz", "pls", "plse", "pleas"],
    "help": ["help", "hlp", "halp", "hellp"],
    "code": ["code", "cod", "cde", "kode"],
    "python": ["python", "pyton", "pythn", "pyhton"],
    "javascript": ["javascript", "js", "javascrpt", "javascritp", "javascrip"],

    # Commands
    "status": ["status", "stats", "stat", "staus", "statsu"],
    "check": ["check", "chek", "chck", "chk"],
    "test": ["test", "tst", "tes"],
    "exit": ["exit", "ext", "quit", "qut", "exti"],

    # Common phrases
    "what is": ["what is", "whats", "what's", "whatis", "wht is", "wat is"],
    "how to": ["how to", "howto", "how 2", "how do i", "how do you"],

    # Bi/By confusion
    "by": ["by", "bi"],
    "bi": ["bi", "by"]
}

# Build reverse lookup dictionary
TYPO_TO_CORRECTION = {}
for correct, variants in COMMON_TYPOS.items():
    for variant in variants:
        if variant != correct:  # Don't map correct words to themselves
            TYPO_TO_CORRECTION[variant] = correct

def correct_typos(text: str) -> Tuple[str, bool]:
    """
    Correct common typos in text

    Args:
        text: Input text to correct

    Returns:
        Tuple of (corrected_text, was_corrected)
    """
    if not text:
        return text, False

    # Lowercase for matching
    lower_text = text.lower()

    # Check if the entire text is a single word that needs correction
    if lower_text in TYPO_TO_CORRECTION:
        corrected = TYPO_TO_CORRECTION[lower_text]
        # Preserve original capitalization if possible
        if text.isupper():
            corrected = corrected.upper()
        elif text[0].isupper():
            corrected = corrected.capitalize()
        return corrected, True

    # Split into words and correct each one
    words = re.findall(r'\b\w+\b', text)
    if not words:
        return text, False

    corrected_text = text
    was_corrected = False

    for word in words:
        lower_word = word.lower()
        if lower_word in TYPO_TO_CORRECTION and lower_word != TYPO_TO_CORRECTION[lower_word]:
            corrected_word = TYPO_TO_CORRECTION[lower_word]

            # Preserve original capitalization
            if word.isupper():
                corrected_word = corrected_word.upper()
            elif word[0].isupper():
                corrected_word = corrected_word.capitalize()

            # Replace in the original text (only replace whole words)
            pattern = r'\b' + re.escape(word) + r'\b'
            corrected_text = re.sub(pattern, corrected_word, corrected_text)
            was_corrected = True

    return corrected_text, was_corrected

def suggest_correction(text: str) -> Optional[str]:
    """
    Suggest a correction for text if needed, but don't apply it

    Args:
        text: Input text to check

    Returns:
        Suggested correction or None if no correction needed
    """
    corrected, was_corrected = correct_typos(text)
    if was_corrected and corrected != text:
        return corrected
    return None
