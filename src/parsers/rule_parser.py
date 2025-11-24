"""Parse VLM output into structured constraint rules."""

import json
import re
import logging
from typing import Dict, Any, List, Optional

from src.core.constraint_rules import (
    ConstraintRuleSet,
    ConstraintRule,
    ConstraintType,
)

logger = logging.getLogger(__name__)


class RuleParser:
    """Parse VLM responses into ConstraintRuleSet."""

    @staticmethod
    def parse_json_from_text(text: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON from VLM response text.

        Handles cases where JSON is embedded in natural language.

        Args:
            text: VLM response text

        Returns:
            Parsed JSON dict or None if parsing fails
        """
        logger.debug(f"Full VLM response:\n{text}")

        # Try to find JSON block
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if not json_match:
            logger.warning("No JSON found in response")
            return None

        json_str = json_match.group(0)
        logger.debug(f"Extracted JSON string:\n{json_str[:500]}")

        try:
            data = json.loads(json_str)
            logger.debug(f"Successfully parsed JSON with {len(data.get('rules', []))} rules")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.error(f"JSON string length: {len(json_str)}")
            logger.error(f"First 500 chars: {json_str[:500]}")
            logger.error(f"Last 500 chars: {json_str[-500:]}")
            return None

    @staticmethod
    def parse_rules_from_json(data: Dict[str, Any]) -> Optional[ConstraintRuleSet]:
        """
        Convert parsed JSON into ConstraintRuleSet.

        Args:
            data: Parsed JSON from VLM response

        Returns:
            ConstraintRuleSet or None if parsing fails
        """
        try:
            rule_set = ConstraintRuleSet()

            # Parse rules
            for rule_data in data.get("rules", []):
                constraint_type = rule_data.get("type", "custom")

                # Validate constraint type
                try:
                    constraint_type = ConstraintType(constraint_type)
                except ValueError:
                    logger.warning(f"Unknown constraint type: {constraint_type}, using custom")
                    constraint_type = ConstraintType.CUSTOM

                # Build scope
                scope = rule_data.get("applies_to", [])
                if not scope and "scope" in rule_data:
                    # Handle alternate scope format
                    scope_val = rule_data["scope"]
                    if isinstance(scope_val, str):
                        # Generate scope from scope type
                        scope = RuleParser._generate_scope_from_type(scope_val)

                # Create rule
                rule = ConstraintRule(
                    constraint_type=constraint_type,
                    scope=scope,
                    parameters={
                        "original_type": rule_data.get("type"),
                        "original_scope": rule_data.get("scope"),
                    },
                    description=rule_data.get("description", ""),
                )
                rule_set.add_rule(rule)

            # Add metadata
            rule_set.metadata = {
                "confidence": data.get("confidence", 0.5),
                "reasoning": data.get("reasoning", ""),
            }

            logger.info(f"Parsed {len(rule_set.rules)} rules")
            return rule_set

        except Exception as e:
            logger.error(f"Failed to parse rules: {e}")
            return None

    @staticmethod
    def _generate_scope_from_type(scope_type: str) -> List[str]:
        """
        Generate variable scope list from scope type string.

        Args:
            scope_type: Type of scope (e.g., "row", "column", "box")

        Returns:
            List of variable names
        """
        if scope_type.lower() == "row":
            return [f"row_{i}" for i in range(9)]
        elif scope_type.lower() in ["column", "col"]:
            return [f"col_{i}" for i in range(9)]
        elif scope_type.lower() == "box":
            return [f"box_{i}" for i in range(9)]
        else:
            return []

    @staticmethod
    def parse_rule_response(text: str) -> Optional[ConstraintRuleSet]:
        """
        Complete pipeline: text → JSON → ConstraintRuleSet.

        Args:
            text: Raw VLM response text

        Returns:
            ConstraintRuleSet or None if parsing fails
        """
        # Extract JSON
        json_data = RuleParser.parse_json_from_text(text)
        if json_data is None:
            return None

        # Parse into rules
        rules = RuleParser.parse_rules_from_json(json_data)
        return rules


def extract_rules_from_vlm_response(vlm_response: str) -> Optional[ConstraintRuleSet]:
    """
    Convenience function to parse VLM response into rules.

    Args:
        vlm_response: Raw text from VLM

    Returns:
        ConstraintRuleSet or None
    """
    return RuleParser.parse_rule_response(vlm_response)
