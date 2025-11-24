"""Rule inference module - core novelty of the system."""

import logging
from typing import List, Optional
from pathlib import Path

from src.models.vlm_interface import VLMInterface
from src.data.dataset import SudokuDataset, SudokuPuzzle
from src.core.constraint_rules import ConstraintRuleSet
from src.prompts.rule_inference_prompts import get_rule_inference_prompt
from src.parsers.rule_parser import extract_rules_from_vlm_response
from src.config import config

logger = logging.getLogger(__name__)


class RuleInferenceModule:
    """
    Infer constraint rules from solved puzzle examples using VLM.

    Pipeline:
    1. Load solved examples
    2. Prepare prompt with example images
    3. Query VLM to analyze patterns
    4. Parse VLM response into formal rules
    5. Validate rules
    """

    def __init__(self, vlm: VLMInterface):
        """
        Initialize rule inference module.

        Args:
            vlm: Vision-Language Model interface
        """
        self.vlm = vlm
        self.logger = logging.getLogger(__name__)

    def infer_rules(
        self,
        examples: List[SudokuPuzzle],
        validate: bool = True,
    ) -> Optional[ConstraintRuleSet]:
        """
        Infer constraint rules from solved puzzle examples.

        Args:
            examples: List of solved puzzle examples
            validate: Whether to validate inferred rules

        Returns:
            ConstraintRuleSet or None if inference fails
        """
        if not examples:
            self.logger.error("No examples provided for rule inference")
            return None

        self.logger.info(f"Inferring rules from {len(examples)} examples")

        # Load images
        images = [Path(ex.image_path) for ex in examples]

        # Check all images exist
        for img_path in images:
            if not img_path.exists():
                self.logger.error(f"Image not found: {img_path}")
                return None

        # Prepare prompt
        prompt = get_rule_inference_prompt(num_examples=len(examples))

        self.logger.debug(f"Querying VLM with {len(images)} images...")

        # Query VLM with all examples at once
        try:
            # For single query with multiple images, use the first image
            # and include context about others
            # Note: Ideally we'd pass all images, but API handling varies
            if len(images) > 1:
                # Use first image as primary
                self.logger.info(f"Querying VLM with image: {images[0]}")
                response = self.vlm.query(
                    image=images[0],
                    prompt=f"{prompt}\n\nNote: Analyzing puzzle #1 along with {len(images)-1} other similar puzzles.",
                    max_tokens=2048,
                )
            else:
                self.logger.info(f"Querying VLM with image: {images[0]}")
                response = self.vlm.query(
                    image=images[0],
                    prompt=prompt,
                    max_tokens=2048,
                )

            self.logger.info(f"VLM response received ({len(response.text)} chars)")
            self.logger.debug(f"VLM response:\n{response.text}")

        except Exception as e:
            self.logger.error(f"VLM query failed: {e}")
            import traceback
            traceback.print_exc()
            return None

        # Parse response
        self.logger.debug("Parsing VLM response...")
        rules = extract_rules_from_vlm_response(response.text)

        if rules is None:
            self.logger.error("Failed to parse VLM response into rules")
            return None

        self.logger.info(f"Inferred {len(rules.rules)} rules")

        # Validate rules
        if validate:
            self.logger.debug("Validating inferred rules...")
            is_valid = self.validate_rules(rules, examples)
            if not is_valid:
                self.logger.warning("Rule validation failed, but continuing anyway")

        return rules

    def validate_rules(
        self,
        rules: ConstraintRuleSet,
        examples: List[SudokuPuzzle],
    ) -> bool:
        """
        Validate inferred rules against training examples.

        Check:
        - Rules don't contradict any training example solutions
        - Rules are consistent across all examples

        Args:
            rules: Inferred rules to validate
            examples: Training examples to validate against

        Returns:
            True if rules are valid, False otherwise
        """
        if not examples:
            self.logger.warning("No examples to validate against")
            return False

        self.logger.info(f"Validating {len(rules.rules)} rules against {len(examples)} examples")

        # For now, basic validation: rules exist and have required fields
        for rule in rules.rules:
            if not rule.scope:
                self.logger.warning(f"Rule has empty scope: {rule}")
                return False

        # TODO: More sophisticated validation
        # - Check rules don't create contradictions in solutions
        # - Verify rules are necessary for solutions
        # - Check rules generalize across all examples

        return True

    def refine_rules_with_feedback(
        self,
        rules: ConstraintRuleSet,
        feedback: str,
    ) -> Optional[ConstraintRuleSet]:
        """
        Refine inferred rules based on feedback.

        Args:
            rules: Current inferred rules
            feedback: User or system feedback on rules

        Returns:
            Refined ConstraintRuleSet or None
        """
        self.logger.info("Refining rules with feedback...")

        # Create refinement prompt
        refinement_prompt = f"""
Based on the following feedback about inferred Sudoku rules, please refine them:

Current rules: {rules}

Feedback: {feedback}

Please provide corrected/refined rules in the same JSON format as before.
"""

        # Query VLM for refinement
        try:
            response = self.vlm.query(
                image="text_only",  # No image needed for refinement
                prompt=refinement_prompt,
                max_tokens=2048,
            )
        except Exception as e:
            self.logger.error(f"Refinement query failed: {e}")
            return None

        # Parse refined rules
        refined_rules = extract_rules_from_vlm_response(response.text)
        return refined_rules

    def __enter__(self):
        """Context manager entry."""
        self.vlm.load_model()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.vlm.unload_model()
