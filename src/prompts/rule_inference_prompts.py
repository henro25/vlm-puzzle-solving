"""Prompt templates for rule inference from solved puzzle examples."""


def get_rule_inference_prompt(num_examples: int = 5) -> str:
    """
    Generate prompt for VLM to infer constraint rules from solved examples.

    Args:
        num_examples: Number of examples that will be shown

    Returns:
        Prompt template string
    """
    return f"""You are analyzing Sudoku puzzles to discover the constraint rules they follow.

Below, you will see {num_examples} solved Sudoku puzzles (complete 9×9 grids filled with digits 1-9).

Examine these puzzles carefully and identify ALL the rules/constraints that:
1. Apply to ALL the puzzles shown
2. Are consistent across all of them
3. Would be necessary to solve ANY Sudoku puzzle

Focus on:
- Row constraints
- Column constraints
- Box constraints (3×3 regions)
- Any other patterns you notice

IMPORTANT: Return your answer as a JSON object with this exact structure:
{{
    "rules": [
        {{
            "type": "all_different",
            "scope": "row",
            "description": "Each row must contain all digits 1-9 exactly once",
            "applies_to": ["row_0", "row_1", "row_2", "row_3", "row_4", "row_5", "row_6", "row_7", "row_8"]
        }},
        {{
            "type": "all_different",
            "scope": "column",
            "description": "Each column must contain all digits 1-9 exactly once",
            "applies_to": ["col_0", "col_1", "col_2", "col_3", "col_4", "col_5", "col_6", "col_7", "col_8"]
        }},
        {{
            "type": "all_different",
            "scope": "box",
            "description": "Each 3×3 box must contain all digits 1-9 exactly once",
            "applies_to": ["box_0", "box_1", "box_2", "box_3", "box_4", "box_5", "box_6", "box_7", "box_8"]
        }}
    ],
    "confidence": 0.95,
    "reasoning": "Explanation of how you discovered these rules"
}}

Rules must have one of these types: all_different, sum, arithmetic, adjacency, custom.

Now analyze the {num_examples} solved puzzles shown below:"""


def get_rule_validation_prompt() -> str:
    """
    Generate prompt to validate inferred rules against a puzzle.

    Returns:
        Prompt template string
    """
    return """You are verifying if the following constraint rules are correct for a Sudoku puzzle.

Given:
1. A set of inferred rules
2. A solved Sudoku puzzle (ground truth)

Check if the rules are:
- Consistent with the solution
- Necessary for solving
- Not too specific to just this puzzle

Return a JSON object:
{
    "valid": true/false,
    "violations": ["list of rule violations if any"],
    "confidence": 0.95,
    "notes": "Any observations"
}"""


def get_few_shot_example() -> str:
    """
    Get an example of expected rule inference output.

    Returns:
        Example JSON output
    """
    return """{
    "rules": [
        {
            "type": "all_different",
            "scope": "row",
            "description": "Each row must contain all digits 1-9 exactly once",
            "applies_to": ["row_0", "row_1", "row_2", "row_3", "row_4", "row_5", "row_6", "row_7", "row_8"]
        },
        {
            "type": "all_different",
            "scope": "column",
            "description": "Each column must contain all digits 1-9 exactly once",
            "applies_to": ["col_0", "col_1", "col_2", "col_3", "col_4", "col_5", "col_6", "col_7", "col_8"]
        },
        {
            "type": "all_different",
            "scope": "box",
            "description": "Each 3×3 box must contain all digits 1-9 exactly once",
            "applies_to": ["box_0", "box_1", "box_2", "box_3", "box_4", "box_5", "box_6", "box_7", "box_8"]
        }
    ],
    "confidence": 0.99,
    "reasoning": "All three rules are fundamental to Sudoku. Row and column constraints ensure no duplicates in any horizontal or vertical line. Box constraints ensure no duplicates in any 3×3 region. These three rule types together define the complete Sudoku puzzle."
}"""
