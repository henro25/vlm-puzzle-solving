"""Data structures for CSP representation."""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
import json
from pathlib import Path


@dataclass
class Variable:
    """A CSP variable."""

    name: str
    domain: List[Any]
    value: Optional[Any] = None

    def is_assigned(self) -> bool:
        """Check if variable has been assigned."""
        return self.value is not None


@dataclass
class Constraint:
    """A CSP constraint."""

    name: str
    scope: List[str]  # Variable names
    predicate: Optional[Callable] = None  # Function to check constraint
    parameters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary (without predicate)."""
        return {
            "name": self.name,
            "scope": self.scope,
            "parameters": self.parameters,
        }


@dataclass
class CSPProblem:
    """Representation of a Constraint Satisfaction Problem."""

    variables: Dict[str, Variable] = field(default_factory=dict)
    constraints: List[Constraint] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_variable(self, name: str, domain: List[Any]) -> None:
        """Add a variable to the CSP."""
        self.variables[name] = Variable(name, domain)

    def add_constraint(
        self,
        name: str,
        scope: List[str],
        predicate: Optional[Callable] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a constraint to the CSP."""
        constraint = Constraint(
            name=name,
            scope=scope,
            predicate=predicate,
            parameters=parameters or {},
        )
        self.constraints.append(constraint)

    def get_variable(self, name: str) -> Optional[Variable]:
        """Get variable by name."""
        return self.variables.get(name)

    def get_unassigned_variables(self) -> List[Variable]:
        """Get all unassigned variables."""
        return [v for v in self.variables.values() if not v.is_assigned()]

    def get_constraints_for_variable(self, var_name: str) -> List[Constraint]:
        """Get all constraints involving a variable."""
        return [c for c in self.constraints if var_name in c.scope]

    def is_consistent(self, variable_name: str, value: Any) -> bool:
        """
        Check if assigning value to variable is consistent with current assignment.
        """
        # Temporarily assign value
        original_value = self.variables[variable_name].value
        self.variables[variable_name].value = value

        # Check all constraints involving this variable
        for constraint in self.get_constraints_for_variable(variable_name):
            # Check if all variables in constraint are assigned
            all_assigned = all(
                self.variables[v].is_assigned() for v in constraint.scope
            )

            if all_assigned and constraint.predicate:
                # Get values for all variables in constraint
                values = {v: self.variables[v].value for v in constraint.scope}

                # Check if constraint is satisfied
                try:
                    if not constraint.predicate(values, constraint.parameters):
                        self.variables[variable_name].value = original_value
                        return False
                except Exception:
                    self.variables[variable_name].value = original_value
                    return False

        self.variables[variable_name].value = original_value
        return True

    def to_dict(self) -> dict:
        """Convert to dictionary (without predicates)."""
        return {
            "variables": {
                name: {"domain": var.domain, "value": var.value}
                for name, var in self.variables.items()
            },
            "constraints": [c.to_dict() for c in self.constraints],
            "metadata": self.metadata,
        }

    def save(self, path: Path) -> None:
        """Save CSP to JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)

    def __str__(self) -> str:
        """String representation."""
        lines = [
            f"CSP Problem:",
            f"  Variables: {len(self.variables)}",
            f"  Constraints: {len(self.constraints)}",
            f"  Assigned: {len([v for v in self.variables.values() if v.is_assigned()])}",
        ]
        return "\n".join(lines)
