"""Data structures for constraint rules."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import json
from pathlib import Path


class ConstraintType(str, Enum):
    """Types of constraints."""
    ALL_DIFFERENT = "all_different"
    SUM = "sum"
    ARITHMETIC = "arithmetic"
    ADJACENCY = "adjacency"
    CUSTOM = "custom"


@dataclass
class ConstraintRule:
    """Represents a single constraint rule."""

    constraint_type: ConstraintType
    scope: List[str]  # Variable names affected
    parameters: Dict[str, Any] = field(default_factory=dict)
    description: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "type": self.constraint_type.value,
            "scope": self.scope,
            "parameters": self.parameters,
            "description": self.description,
        }

    @staticmethod
    def from_dict(data: dict) -> "ConstraintRule":
        """Create from dictionary."""
        return ConstraintRule(
            constraint_type=ConstraintType(data["type"]),
            scope=data["scope"],
            parameters=data.get("parameters", {}),
            description=data.get("description", ""),
        )


@dataclass
class VariableSpec:
    """Specification for a variable in the CSP."""

    name: str
    domain: List[Any]
    description: str = ""


@dataclass
class ConstraintRuleSet:
    """Set of inferred constraint rules."""

    rules: List[ConstraintRule] = field(default_factory=list)
    variables: Dict[str, VariableSpec] = field(default_factory=dict)
    domains: Dict[str, List[Any]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_rule(self, rule: ConstraintRule) -> None:
        """Add a constraint rule."""
        self.rules.append(rule)

    def add_variable(self, name: str, domain: List[Any], description: str = "") -> None:
        """Add a variable specification."""
        self.variables[name] = VariableSpec(name, domain, description)
        self.domains[name] = domain

    def get_rules_for_variable(self, var_name: str) -> List[ConstraintRule]:
        """Get all rules affecting a variable."""
        return [r for r in self.rules if var_name in r.scope]

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "rules": [r.to_dict() for r in self.rules],
            "variables": {
                name: {
                    "domain": var.domain,
                    "description": var.description,
                }
                for name, var in self.variables.items()
            },
            "domains": {name: domain for name, domain in self.domains.items()},
            "metadata": self.metadata,
        }

    @staticmethod
    def from_dict(data: dict) -> "ConstraintRuleSet":
        """Create from dictionary."""
        rule_set = ConstraintRuleSet()

        # Add rules
        for rule_data in data.get("rules", []):
            rule_set.add_rule(ConstraintRule.from_dict(rule_data))

        # Add variables
        for name, var_data in data.get("variables", {}).items():
            rule_set.add_variable(
                name,
                var_data["domain"],
                var_data.get("description", ""),
            )

        # Add metadata
        rule_set.metadata = data.get("metadata", {})

        return rule_set

    def save(self, path: Path) -> None:
        """Save rules to JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @staticmethod
    def load(path: Path) -> "ConstraintRuleSet":
        """Load rules from JSON file."""
        with open(path, "r") as f:
            data = json.load(f)
        return ConstraintRuleSet.from_dict(data)

    def __str__(self) -> str:
        """String representation of rules."""
        lines = ["Constraint Rules:"]
        for i, rule in enumerate(self.rules, 1):
            lines.append(f"  {i}. {rule.constraint_type.value} on {rule.scope}")
            if rule.description:
                lines.append(f"     {rule.description}")
        return "\n".join(lines)
