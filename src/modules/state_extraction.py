"""State extraction module - extract puzzle state from images."""

import logging
from pathlib import Path
from typing import Optional

from src.models.vlm_interface import VLMInterface
from src.core.puzzle_state import PuzzleState
from src.prompts.state_extraction_prompts import (
    get_state_extraction_prompt,
    get_state_correction_prompt,
)
from src.parsers.state_parser import extract_state_from_vlm_response, StateParser

logger = logging.getLogger(__name__)


class StateExtractionModule:
    """
    Extract puzzle state from puzzle images using VLM.

    Pipeline:
    1. Load puzzle image
    2. Prepare extraction prompt
    3. Query VLM to extract cell values
    4. Parse VLM response into PuzzleState
    5. Validate extracted state
    6. Optionally refine with corrections
    """

    def __init__(self, vlm: VLMInterface):
        """
        Initialize state extraction module.

        Args:
            vlm: Vision-Language Model interface
        """
        self.vlm = vlm
        self.logger = logging.getLogger(__name__)

    def extract_state(
        self,
        puzzle_image: Path,
        validate: bool = True,
        auto_correct: bool = False,
    ) -> Optional[PuzzleState]:
        """
        Extract puzzle state from image.

        Args:
            puzzle_image: Path to puzzle image
            validate: Whether to validate extracted state
            auto_correct: Whether to auto-correct issues

        Returns:
            PuzzleState or None if extraction fails
        """
        puzzle_image = Path(puzzle_image)

        if not puzzle_image.exists():
            self.logger.error(f"Image not found: {puzzle_image}")
            return None

        self.logger.info(f"Extracting state from: {puzzle_image}")

        # Prepare prompt
        prompt = get_state_extraction_prompt()

        # Query VLM
        self.logger.debug("Querying VLM for state extraction...")
        try:
            response = self.vlm.query(
                image=puzzle_image,
                prompt=prompt,
                max_tokens=2048,
            )
            self.logger.info(f"VLM response received ({len(response.text)} chars)")
            self.logger.debug(f"VLM response:\n{response.text[:500]}")

        except Exception as e:
            self.logger.error(f"VLM query failed: {e}")
            import traceback
            traceback.print_exc()
            return None

        # Parse response
        self.logger.debug("Parsing VLM response...")
        state = extract_state_from_vlm_response(response.text)

        if state is None:
            self.logger.error("Failed to parse VLM response into state")
            return None

        self.logger.info(f"Extracted state: {len(state.filled_cells)} filled, {len(state.empty_cells)} empty")

        # Validate state
        if validate:
            self.logger.debug("Validating extracted state...")
            report = StateParser.validate_state(state)

            if not report["valid"]:
                self.logger.warning(f"State validation issues: {report['issues']}")

                if auto_correct:
                    self.logger.info("Attempting to auto-correct state...")
                    state = self._auto_correct_state(state, report, puzzle_image)

        return state

    def _auto_correct_state(
        self,
        state: PuzzleState,
        validation_report: dict,
        puzzle_image: Path,
    ) -> Optional[PuzzleState]:
        """
        Auto-correct state based on validation issues.

        Args:
            state: Current state with issues
            validation_report: Validation report
            puzzle_image: Original puzzle image

        Returns:
            Corrected PuzzleState or None
        """
        issues = validation_report.get("issues", [])

        # Extract problematic cells from issues
        problematic_cells = []
        for issue in issues:
            # Parse issue descriptions to find cell indices
            # Format: "Duplicate values in row 0" or "Duplicate values in column 3"
            if "row" in issue.lower():
                try:
                    row_idx = int(issue.split()[-1])
                    for col in range(9):
                        problematic_cells.append(f"{row_idx},{col}")
                except (ValueError, IndexError):
                    pass
            elif "column" in issue.lower():
                try:
                    col_idx = int(issue.split()[-1])
                    for row in range(9):
                        problematic_cells.append(f"{row},{col_idx}")
                except (ValueError, IndexError):
                    pass

        if not problematic_cells:
            self.logger.warning("Could not identify problematic cells")
            return state

        self.logger.info(f"Re-examining {len(problematic_cells)} cells...")

        # Get correction prompt
        prompt = get_state_correction_prompt(problematic_cells[:10])  # Limit to 10 cells

        try:
            response = self.vlm.query(
                image=puzzle_image,
                prompt=prompt,
                max_tokens=1024,
            )

            # Parse corrections
            import json
            import re
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                corrections_data = json.loads(json_match.group(0))
                corrections = corrections_data.get("corrections", [])

                # Apply corrections
                for correction in corrections:
                    row, col = correction["row"], correction["col"]
                    status = correction.get("status", "").lower()
                    value = correction.get("value")

                    if status == "filled" and value:
                        state.set_cell_value(row, col, int(value))
                    elif status == "empty" and (row, col) in state.filled_cells:
                        del state.filled_cells[(row, col)]

                self.logger.info(f"Applied {len(corrections)} corrections")

        except Exception as e:
            self.logger.warning(f"Auto-correction failed: {e}")

        return state

    def __enter__(self):
        """Context manager entry."""
        self.vlm.load_model()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.vlm.unload_model()
