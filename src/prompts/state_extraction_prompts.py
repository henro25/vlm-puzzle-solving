"""Prompt templates for state extraction from puzzle images."""


def get_state_extraction_prompt() -> str:
    """
    Generate prompt for VLM to extract puzzle state from image.

    Returns:
        Prompt template string
    """
    return """You are extracting the current state of a Sudoku puzzle from an image.

Carefully examine the image and identify:
1. The current state of all 81 cells (9×9 grid)
2. Which cells are filled (contain digits 1-9)
3. Which cells are empty (blank)
4. The exact values in filled cells

Return your answer as a JSON object with this exact structure:
{
    "grid_size": [9, 9],
    "filled_cells": [
        {"row": 0, "col": 0, "value": 5},
        {"row": 0, "col": 1, "value": 3},
        {"row": 0, "col": 2, "value": 4},
        ...
    ],
    "empty_cells": [
        {"row": 0, "col": 3},
        {"row": 0, "col": 4},
        ...
    ],
    "confidence": 0.95,
    "notes": "Any observations about image clarity or potential misreadings"
}

IMPORTANT GUIDELINES:
- Row and column indices are 0-indexed (0-8)
- Include ALL 81 cells (either in filled_cells or empty_cells)
- Values must be digits 1-9
- Double-check digit recognition carefully
- If any cell is unclear, note it in the "notes" field
- Confidence should reflect your certainty (0.0-1.0)

Now analyze the Sudoku puzzle image below:"""


def get_state_validation_prompt() -> str:
    """
    Generate prompt to validate extracted state.

    Returns:
        Prompt template string
    """
    return """You are verifying an extracted Sudoku puzzle state.

Given an extracted state and the original image, verify:
1. All 81 cells are accounted for
2. Filled cell values match the image
3. No contradictions (same value twice in a row/col/box)
4. Image quality/clarity assessment

Return JSON:
{
    "valid": true/false,
    "issues": ["list of issues if any"],
    "cell_accuracy": 0.95,
    "confidence": 0.95,
    "notes": "Any observations"
}"""


def get_state_correction_prompt(problematic_cells: list) -> str:
    """
    Generate prompt to re-examine specific cells.

    Args:
        problematic_cells: List of cells to re-examine (format: "row,col")

    Returns:
        Prompt template string
    """
    cells_str = ", ".join(problematic_cells)
    return f"""Please re-examine the following cells in the Sudoku puzzle image:
{cells_str}

Look very carefully at each cell and verify:
1. Whether it's filled or empty
2. If filled, what digit it contains (1-9)
3. Image clarity/contrast for that cell

Return corrected information in JSON format:
{{
    "corrections": [
        {{"row": 0, "col": 3, "status": "empty or filled", "value": null or digit}},
        ...
    ],
    "confidence": 0.95
}}"""
