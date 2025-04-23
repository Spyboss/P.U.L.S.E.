"""
Tests for the spell correction utility
"""

import unittest
from utils.spell_correction import correct_typos, suggest_correction

class TestSpellCorrection(unittest.TestCase):
    """Test cases for spell correction utility"""

    def test_correct_typos(self):
        """Test correcting typos in text"""
        # Test simple corrections
        self.assertEqual(correct_typos("hi")[0], "hi")
        self.assertEqual(correct_typos("helo")[0], "hello")
        self.assertEqual(correct_typos("thnx")[0], "thanks")
        self.assertEqual(correct_typos("plz")[0], "please")

        # Test capitalization preservation
        self.assertEqual(correct_typos("Helo")[0], "Hello")
        self.assertEqual(correct_typos("HELO")[0], "HELLO")

        # Test phrases
        self.assertEqual(correct_typos("helo there, how r u?")[0], "hello there, how r u?")
        self.assertEqual(correct_typos("plz help me with my cod")[0], "please help me with my code")

        # Test was_corrected flag
        # Note: "hello" is in the variants list for "hi", so it might be corrected
        self.assertEqual(correct_typos("normal text")[1], False)  # No correction needed
        self.assertEqual(correct_typos("helo")[1], True)    # Correction made

        # Test bi/by confusion
        self.assertEqual(correct_typos("bi bruv!")[0], "by bruv!")
        self.assertEqual(correct_typos("come bi later")[0], "come by later")

    def test_suggest_correction(self):
        """Test suggesting corrections"""
        # Test suggestions
        self.assertEqual(suggest_correction("helo"), "hello")
        self.assertEqual(suggest_correction("thnx"), "thanks")

        # Test no suggestion needed
        self.assertIsNone(suggest_correction("normal text"))
        self.assertIsNone(suggest_correction("computer"))

        # Test phrases
        self.assertEqual(suggest_correction("plz help"), "please help")

if __name__ == "__main__":
    unittest.main()
