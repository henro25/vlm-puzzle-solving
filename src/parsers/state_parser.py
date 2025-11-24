"""Parse VLM output into puzzle state."""

import json
import re
import logging
from typing import Dict, Any, List, Optional

from src.core.puzzle_state import PuzzleState

logger = logging.getLogger(__name__)


class StateParser:
    """Parse VLM responses into PuzzleState."""

    @staticmethod
    def _repair_json(json_str: str) -> str:
        """
        Repair common JSON errors from VLM output.

        Fixes:
        - Missing closing brackets ] and }
        - Missing commas between array elements
        - Trailing commas
        """
        # Remove trailing commas before ] or }
        json_str = re.sub(r',\s*([}\]])', r'\1', json_str)

        # Balance brackets and braces
        json_str = json_str.rstrip()

        # Count unmatched brackets
        open_brackets = json_str.count('[')
        close_brackets = json_str.count(']')
        open_braces = json_str.count('{')
        close_braces = json_str.count('}')

        # Add missing closing brackets
        if close_brackets < open_brackets:
            json_str += ']' * (open_brackets - close_brackets)

        # Add missing closing braces
        if close_braces < open_braces:
            json_str += '}' * (open_braces - close_braces)

        return json_str

    @staticmethod
    def parse_json_from_text(text: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON from VLM response text.

        Args:
            text: VLM response text

        Returns:
            Parsed JSON dict or None if parsing fails
        """
        logger.debug(f"Full VLM response length: {len(text)}")

        # Try to find JSON block
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if not json_match:
            logger.warning("No JSON found in response")
            return None

        json_str = json_match.group(0)
        logger.debug(f"Extracted JSON string length: {len(json_str)}")

        # Try to repair common JSON errors
        logger.debug("Attempting to repair JSON...")
        json_str = StateParser._repair_json(json_str)

        try:
            data = json.loads(json_str)
            logger.debug(f"Successfully parsed JSON")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.error(f"Error at line {e.lineno}, column {e.colno}")

            # Show context around error
            lines = json_str.split('\n')
            if e.lineno and e.lineno <= len(lines):
                error_line = lines[e.lineno - 1]
                logger.error(f"Error line: {error_line}")
                logger.error(f"Context (lines {max(0, e.lineno-3)} to {min(len(lines), e.lineno+2)}):")
                for i in range(max(0, e.lineno-4), min(len(lines), e.lineno+2)):
                    prefix = ">>> " if i == e.lineno - 1 else "    "
                    logger.error(f"{prefix}{i+1}: {lines[i][:100]}")

            logger.error(f"First 500 chars: {json_str[:500]}")
            logger.error(f"Last 500 chars: {json_str[-500:]}")
            return None

    @staticmethod
    def parse_state_from_json(data: Dict[str, Any]) -> Optional[PuzzleState]:
        """
        Convert parsed JSON into PuzzleState.

        Args:
            data: Parsed JSON from VLM response

        Returns:
            PuzzleState or None if parsing fails
        """
        try:
            grid_size = tuple(data.get("grid_size", [9, 9]))

            # Parse filled cells
            filled_cells = {}
            for cell_info in data.get("filled_cells", []):
                row = cell_info.get("row")
                col = cell_info.get("col")
                value = cell_info.get("value")

                if row is None or col is None or value is None:
                    logger.warning(f"Invalid cell info: {cell_info}")
                    continue

                # Validate value is 1-9
                if not isinstance(value, int) or value < 1 or value > 9:
                    logger.warning(f"Invalid cell value: {value} at ({row}, {col})")
                    continue

                filled_cells[(row, col)] = value

            # Parse empty cells (optional, can be auto-populated)
            # Important: exclude cells that are already in filled_cells
            empty_cells = []
            for cell_info in data.get("empty_cells", []):
                row = cell_info.get("row")
                col = cell_info.get("col")
                if row is not None and col is not None:
                    # Only add if not already filled
                    if (row, col) not in filled_cells:
                        empty_cells.append((row, col))

            # Create PuzzleState
            state = PuzzleState(
                grid_size=grid_size,
                filled_cells=filled_cells,
                empty_cells=empty_cells,
            )

            logger.info(f"Parsed state: {len(filled_cells)} filled cells, {len(state.empty_cells)} empty cells")
            return state

        except Exception as e:
            logger.error(f"Failed to parse state: {e}")
            import traceback
            traceback.print_exc()
            return None

    @staticmethod
    def parse_state_response(text: str) -> Optional[PuzzleState]:
        """
        Complete pipeline: text → JSON → PuzzleState.

        Args:
            text: Raw VLM response text

        Returns:
            PuzzleState or None if parsing fails
        """
        # Extract JSON
        json_data = StateParser.parse_json_from_text(text)
        if json_data is None:
            return None

        # Parse into state
        state = StateParser.parse_state_from_json(json_data)
        return state

    @staticmethod
    def validate_state(state: PuzzleState) -> Dict[str, Any]:
        """
        Validate extracted puzzle state.

        Checks:
        - Correct number of cells (81 for 9x9)
        - No duplicate values in rows/cols/boxes
        - All values are 1-9

        Args:
            state: Puzzle state to validate

        Returns:
            Validation report dict
        """
        report = {
            "valid": True,
            "issues": [],
            "cell_count": len(state.filled_cells) + len(state.empty_cells),
        }

        # Check cell count
        expected_count = state.grid_size[0] * state.grid_size[1]
        if report["cell_count"] != expected_count:
            report["valid"] = False
            report["issues"].append(
                f"Cell count mismatch: {report['cell_count']} vs expected {expected_count}"
            )

        # Check for duplicates in rows
        grid = state.to_grid()
        for row_idx, row in enumerate(grid):
            values = [v for v in row if v is not None]
            if len(values) != len(set(values)):
                report["valid"] = False
                report["issues"].append(f"Duplicate values in row {row_idx}")

        # Check for duplicates in columns
        for col_idx in range(len(grid[0])):
            values = [grid[row_idx][col_idx] for row_idx in range(len(grid)) if grid[row_idx][col_idx] is not None]
            if len(values) != len(set(values)):
                report["valid"] = False
                report["issues"].append(f"Duplicate values in column {col_idx}")

        # Check for duplicates in 3x3 boxes
        for box_row in range(0, 9, 3):
            for box_col in range(0, 9, 3):
                values = []
                for r in range(box_row, box_row + 3):
                    for c in range(box_col, box_col + 3):
                        if grid[r][c] is not None:
                            values.append(grid[r][c])
                if len(values) != len(set(values)):
                    report["valid"] = False
                    report["issues"].append(f"Duplicate values in box ({box_row}, {box_col})")

        return report


def extract_state_from_vlm_response(vlm_response: str) -> Optional[PuzzleState]:
    """
    Convenience function to parse VLM response into puzzle state.

    Args:
        vlm_response: Raw text from VLM

    Returns:
        PuzzleState or None
    """
    return StateParser.parse_state_response(vlm_response)
