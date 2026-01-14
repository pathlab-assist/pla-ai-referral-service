"""Test name preprocessing for improved matching.

This module handles:
1. Compound test splitting (e.g., "Vit B12/Folate" → ["B12", "FOL"])
2. Abbreviation expansion (e.g., "Vit" → "Vitamin", "FBE" → "FBC")
3. Panel recognition (e.g., "EIFT" → ["UEC", "IRON", "FERR", "TFT"])
"""

import re
from typing import List

from app.core.logging import get_logger

logger = get_logger(__name__)


class TestPreprocessor:
    """Preprocessor for test names before catalog matching."""

    # Common abbreviation mappings for Australian pathology
    ABBREVIATION_MAP = {
        # Vitamin abbreviations
        "Vit": "Vitamin",
        "Vit.": "Vitamin",

        # Common test abbreviations
        "FBE": "FBC",  # Full Blood Examination → Full Blood Count
        "Hb": "Haemoglobin",
        "Hgb": "Haemoglobin",
        "WCC": "WBC",  # White Cell Count → White Blood Count
        "RCC": "RBC",  # Red Cell Count → Red Blood Count

        # Electrolytes/Biochemistry
        "U&E": "UEC",
        "E/LFT": "EUC/LFT",
        "Na": "Sodium",
        "K": "Potassium",
        "Ca": "Calcium",
        "Mg": "Magnesium",

        # Liver function
        "LFT's": "LFT",
        "LFTS": "LFT",

        # Thyroid
        "TFT's": "TFT",
        "TFTS": "TFT",
    }

    # Common test panels - when these are mentioned, they mean multiple tests
    PANEL_MAP = {
        "EIFT": ["UEC", "IRON", "FERR", "TFT"],  # Electrolytes/Iron/Ferritin/Thyroid
        "Cardiac Panel": ["TROP", "BNP", "CK", "CKMB"],
        "Anemia Panel": ["FBC", "IRON", "FERR", "B12", "FOL"],
        "Diabetes Panel": ["HBA1C", "GLUCOSE", "FRUCTOSAMINE"],
        "Lipid Panel": ["CHOL", "TRIG", "HDL", "LDL"],
        "Liver Panel": ["LFT", "GGT", "ALP"],
        "Renal Panel": ["UEC", "CREAT", "eGFR"],
    }

    # Compound test separators (in order of precedence)
    COMPOUND_SEPARATORS = [
        "/",  # Most common: "B12/Folate", "UEC/LFT"
        " & ",  # "Iron & TIBC"
        " and ",  # "B12 and Folate"
        "+",  # "FBC+UEC"
        ",",  # "B12, Folate"
    ]

    def preprocess(self, test_name: str) -> List[str]:
        """Preprocess a test name into one or more searchable terms.

        Args:
            test_name: Raw test name from referral

        Returns:
            List of preprocessed test names (may be multiple if compound)
        """
        if not test_name or not test_name.strip():
            return []

        original = test_name.strip()

        logger.debug(f"Preprocessing test name: {original}")

        # Step 1: Check for panel recognition (exact match)
        panel_tests = self._recognize_panel(original)
        if panel_tests:
            logger.info(f"Recognized panel '{original}' → {panel_tests}")
            return panel_tests

        # Step 2: Check for compound tests (contains separators)
        compound_tests = self._split_compound(original)
        if len(compound_tests) > 1:
            logger.info(f"Split compound test '{original}' → {compound_tests}")
            # Recursively preprocess each part (they might have abbreviations)
            result = []
            for part in compound_tests:
                result.extend(self.preprocess(part))
            return result

        # Step 3: Expand abbreviations
        expanded = self._expand_abbreviations(original)
        if expanded != original:
            logger.debug(f"Expanded abbreviations '{original}' → '{expanded}'")
            return [expanded]

        # Step 4: Return original if no preprocessing needed
        return [original]

    def _recognize_panel(self, test_name: str) -> List[str]:
        """Recognize if test name is a known panel.

        Args:
            test_name: Test name to check

        Returns:
            List of individual test codes if panel recognized, empty list otherwise
        """
        # Case-insensitive panel matching
        test_upper = test_name.upper().strip()

        for panel_name, panel_tests in self.PANEL_MAP.items():
            if test_upper == panel_name.upper():
                return panel_tests

        return []

    def _split_compound(self, test_name: str) -> List[str]:
        """Split compound test names into individual tests.

        Examples:
            "Vit B12/Folate" → ["Vit B12", "Folate"]
            "UEC/LFT" → ["UEC", "LFT"]
            "FBC+UEC+LFT" → ["FBC", "UEC", "LFT"]

        Args:
            test_name: Test name to split

        Returns:
            List of individual test names (single item if not compound)
        """
        # Try each separator in order of precedence
        for separator in self.COMPOUND_SEPARATORS:
            if separator in test_name:
                # Split and strip whitespace
                parts = [part.strip() for part in test_name.split(separator)]
                # Filter out empty parts
                parts = [part for part in parts if part]
                if len(parts) > 1:
                    return parts

        # Not a compound test
        return [test_name]

    def _expand_abbreviations(self, test_name: str) -> str:
        """Expand common abbreviations in test names.

        Examples:
            "Vit D" → "Vitamin D"
            "FBE" → "FBC"
            "U&E" → "UEC"

        Args:
            test_name: Test name with possible abbreviations

        Returns:
            Test name with abbreviations expanded
        """
        result = test_name

        # Try exact match first (for standalone abbreviations like "FBE")
        if result in self.ABBREVIATION_MAP:
            return self.ABBREVIATION_MAP[result]

        # Replace abbreviations that appear as words (with word boundaries)
        for abbrev, expansion in self.ABBREVIATION_MAP.items():
            # Use word boundary regex to avoid partial matches
            # e.g., "Vit D" matches but "Vital" doesn't
            pattern = r'\b' + re.escape(abbrev) + r'\b'
            result = re.sub(pattern, expansion, result, flags=re.IGNORECASE)

        return result

    def is_compound_test(self, test_name: str) -> bool:
        """Check if a test name is a compound test.

        Args:
            test_name: Test name to check

        Returns:
            True if compound test, False otherwise
        """
        for separator in self.COMPOUND_SEPARATORS:
            if separator in test_name:
                return True
        return False

    def get_panel_tests(self, panel_name: str) -> List[str]:
        """Get individual tests for a panel name.

        Args:
            panel_name: Panel name to look up

        Returns:
            List of test codes, or empty list if not a panel
        """
        panel_upper = panel_name.upper().strip()

        for name, tests in self.PANEL_MAP.items():
            if panel_upper == name.upper():
                return tests

        return []
