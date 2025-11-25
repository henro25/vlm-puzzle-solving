"""Translate constraint rules and puzzle state into CSP."""

import logging
from typing import Optional, Callable, Dict, Any, List

from src.core.constraint_rules import ConstraintRuleSet, ConstraintType
from src.core.puzzle_state import PuzzleState
from src.core.csp_problem import CSPProblem

logger = logging.getLogger(__name__)


class CSPTranslator:
    """
    Translate inferred rules and puzzle state into a Constraint Satisfaction Problem.

    Pipeline:
    1. Create CSP variables for each cell
    2. Set domains (filled cells have fixed value, empty cells have range 1-9)
    3. Add constraints from inferred rules
    4. Return solvable CSPProblem
    """

    @staticmethod
    def translate(
        rules: ConstraintRuleSet,
        state: PuzzleState,
    ) -> Optional[CSPProblem]:
        """
        Translate rules and state into CSP.

        Args:
            rules: Inferred constraint rules
            state: Extracted puzzle state

        Returns:
            CSPProblem or None if translation fails
        """
        logger.info("Translating rules + state into CSP...")

        try:
            csp = CSPProblem()

            # Step 1: Add variables for each cell
            logger.debug("Adding variables...")
            CSPTranslator._add_variables(csp, state)

            # Step 2: Add constraints from rules
            logger.debug("Adding constraints...")
            CSPTranslator._add_constraints(csp, rules, state)

            logger.info(f"CSP created: {len(csp.variables)} variables, {len(csp.constraints)} constraints")
            return csp

        except Exception as e:
            logger.error(f"Translation failed: {e}")
            import traceback
            traceback.print_exc()
            return None

    @staticmethod
    def _add_variables(csp: CSPProblem, state: PuzzleState) -> None:
        """Add variables to CSP from puzzle state."""
        rows, cols = state.grid_size

        for row in range(rows):
            for col in range(cols):
                var_name = f"cell_{row}_{col}"

                # Filled cells have fixed domain
                if (row, col) in state.filled_cells:
                    value = state.filled_cells[(row, col)]
                    csp.add_variable(var_name, [value])
                    logger.debug(f"Added filled variable {var_name} = {value}")
                else:
                    # Empty cells have full domain
                    domain = state.get_domain(row, col)
                    csp.add_variable(var_name, domain)
                    logger.debug(f"Added empty variable {var_name} with domain {domain}")

    @staticmethod
    def _add_constraints(
        csp: CSPProblem,
        rules: ConstraintRuleSet,
        state: PuzzleState,
    ) -> None:
        """Add constraints to CSP from rules."""
        for rule in rules.rules:
            constraint_name = f"{rule.constraint_type.value}_{len(csp.constraints)}"

            if rule.constraint_type == ConstraintType.ALL_DIFFERENT:
                CSPTranslator._add_all_different_constraint(
                    csp, constraint_name, rule.scope
                )
            elif rule.constraint_type == ConstraintType.SUM:
                CSPTranslator._add_sum_constraint(
                    csp, constraint_name, rule.scope, rule.parameters
                )
            elif rule.constraint_type == ConstraintType.ARITHMETIC:
                CSPTranslator._add_arithmetic_constraint(
                    csp, constraint_name, rule.scope, rule.parameters
                )
            else:
                logger.warning(f"Skipping unsupported constraint type: {rule.constraint_type}")

    @staticmethod
    def _add_all_different_constraint(
        csp: CSPProblem,
        constraint_name: str,
        scope: List[str],
    ) -> None:
        """Add all_different constraint."""
        # Convert scope from "row_0" format to variable names
        variable_names = CSPTranslator._convert_scope_to_variables(scope)

        if not variable_names:
            logger.warning(f"Empty variable list for constraint {constraint_name}")
            return

        def all_different_predicate(assignment: Dict[str, int], params: Dict[str, Any]) -> bool:
            """Check that all variables have different values."""
            values = [assignment.get(var) for var in variable_names if var in assignment]
            if len(values) < len(variable_names):
                # Not all variables assigned yet
                return True
            return len(values) == len(set(values))

        csp.add_constraint(
            name=constraint_name,
            scope=variable_names,
            predicate=all_different_predicate,
            parameters={},
        )
        logger.debug(f"Added all_different constraint on {len(variable_names)} variables")

    @staticmethod
    def _add_sum_constraint(
        csp: CSPProblem,
        constraint_name: str,
        scope: List[str],
        parameters: Dict[str, Any],
    ) -> None:
        """Add sum constraint."""
        target_sum = parameters.get("sum", 0)
        variable_names = CSPTranslator._convert_scope_to_variables(scope)

        if not variable_names:
            logger.warning(f"Empty variable list for sum constraint")
            return

        def sum_predicate(assignment: Dict[str, int], params: Dict[str, Any]) -> bool:
            """Check that variables sum to target."""
            values = [assignment.get(var) for var in variable_names if var in assignment]
            if len(values) < len(variable_names):
                return True
            return sum(values) == params.get("sum", 0)

        csp.add_constraint(
            name=constraint_name,
            scope=variable_names,
            predicate=sum_predicate,
            parameters={"sum": target_sum},
        )
        logger.debug(f"Added sum constraint (target={target_sum})")

    @staticmethod
    def _add_arithmetic_constraint(
        csp: CSPProblem,
        constraint_name: str,
        scope: List[str],
        parameters: Dict[str, Any],
    ) -> None:
        """Add arithmetic constraint (generic)."""
        variable_names = CSPTranslator._convert_scope_to_variables(scope)

        if not variable_names:
            logger.warning(f"Empty variable list for arithmetic constraint")
            return

        # Generic arithmetic constraint (can be customized)
        def arithmetic_predicate(assignment: Dict[str, int], params: Dict[str, Any]) -> bool:
            return True  # Placeholder

        csp.add_constraint(
            name=constraint_name,
            scope=variable_names,
            predicate=arithmetic_predicate,
            parameters=parameters,
        )
        logger.debug(f"Added arithmetic constraint")

    @staticmethod
    def _convert_scope_to_variables(scope: List[str]) -> List[str]:
        """
        Convert scope notation to variable names.

        Examples:
            ["row_0"] → ["cell_0_0", "cell_0_1", ..., "cell_0_8"]
            ["col_3"] → ["cell_0_3", "cell_1_3", ..., "cell_8_3"]
            ["box_0"] → ["cell_0_0", "cell_0_1", ..., "cell_2_2"]
        """
        variable_names = []

        for item in scope:
            if item.startswith("row_"):
                row_idx = int(item.split("_")[1])
                for col in range(9):
                    variable_names.append(f"cell_{row_idx}_{col}")

            elif item.startswith("col_"):
                col_idx = int(item.split("_")[1])
                for row in range(9):
                    variable_names.append(f"cell_{row}_{col_idx}")

            elif item.startswith("box_"):
                box_idx = int(item.split("_")[1])
                box_row = (box_idx // 3) * 3
                box_col = (box_idx % 3) * 3
                for r in range(box_row, box_row + 3):
                    for c in range(box_col, box_col + 3):
                        variable_names.append(f"cell_{r}_{c}")

            elif item.startswith("cell_"):
                variable_names.append(item)
            else:
                logger.warning(f"Unknown scope format: {item}")

        return variable_names
