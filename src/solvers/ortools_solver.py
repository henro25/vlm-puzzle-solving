"""Fast CSP solver using Google's OR-Tools library."""

import logging
import time
from typing import Optional, Dict, Any, List

try:
    from ortools.sat.python import cp_model
except ImportError:
    cp_model = None

from src.core.csp_problem import CSPProblem

logger = logging.getLogger(__name__)


class ORToolsSolver:
    """
    Solve Constraint Satisfaction Problems using Google's OR-Tools.

    Provides significant speedup over python-constraint for Sudoku-like problems.

    Supports:
    - CP-SAT solver with efficient propagation
    - Configurable timeouts
    - Parallel solving
    """

    def __init__(self, timeout: int = 60, num_workers: int = 1):
        """
        Initialize OR-Tools solver.

        Args:
            timeout: Maximum solving time in seconds
            num_workers: Number of parallel workers
        """
        self.timeout = timeout
        self.num_workers = num_workers

        if cp_model is None:
            raise ImportError("ortools not installed. Run: pip install ortools")

    def solve(self, csp_problem: CSPProblem) -> Optional[Dict[str, int]]:
        """
        Solve CSP and return first solution.

        Args:
            csp_problem: CSPProblem to solve

        Returns:
            Solution dict {variable_name: value} or None if unsolvable
        """
        logger.info(
            f"Solving CSP with {len(csp_problem.variables)} variables, "
            f"{len(csp_problem.constraints)} constraints using OR-Tools"
        )

        try:
            model = self._build_ortools_model(csp_problem)

            if model is None:
                logger.error("Failed to build OR-Tools model")
                return None

            # Solve with timeout
            start_time = time.time()
            solver = cp_model.CpSolver()
            solver.parameters.max_time_in_seconds = self.timeout
            solver.parameters.num_workers = self.num_workers
            # Enable logging for debugging
            solver.parameters.log_search_progress = False

            status = solver.Solve(model)
            elapsed = time.time() - start_time

            # Map status codes
            status_names = {
                0: "OPTIMAL",
                1: "FEASIBLE",
                2: "INFEASIBLE",
                3: "MODEL_INVALID",
            }
            status_name = status_names.get(status, f"UNKNOWN({status})")

            if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                logger.warning(
                    f"No solution found (status: {status_name}, time: {elapsed:.2f}s). "
                    f"Puzzle may be unsolvable or OR-Tools model is incomplete."
                )
                return None

            # Extract solution
            solution = {}
            for var_name, cp_var in self.var_map.items():
                solution[var_name] = solver.Value(cp_var)

            logger.info(f"Solution found in {elapsed:.2f}s (status: {status_name})")
            return solution

        except Exception as e:
            logger.error(f"Solver error: {e}")
            import traceback
            traceback.print_exc()
            return None

    def solve_with_timeout(
        self, csp_problem: CSPProblem, timeout: int
    ) -> Optional[Dict[str, int]]:
        """
        Solve with custom timeout.

        Args:
            csp_problem: CSPProblem to solve
            timeout: Timeout in seconds

        Returns:
            Solution or None
        """
        original_timeout = self.timeout
        self.timeout = timeout
        try:
            return self.solve(csp_problem)
        finally:
            self.timeout = original_timeout

    def _build_ortools_model(self, csp_problem: CSPProblem) -> Optional[Any]:
        """
        Build OR-Tools CP model from CSPProblem.

        Args:
            csp_problem: CSPProblem to convert

        Returns:
            cp_model.CpModel or None if conversion fails
        """
        try:
            model = cp_model.CpModel()
            self.var_map = {}

            # Create decision variables
            logger.debug("Creating decision variables...")
            for var_name, variable in csp_problem.variables.items():
                domain = variable.domain

                # For Sudoku and similar problems, domain is typically [1-9]
                # OR-Tools requires contiguous domains, so we use min/max
                min_val = min(domain)
                max_val = max(domain)

                cp_var = model.NewIntVar(min_val, max_val, var_name)
                self.var_map[var_name] = cp_var

                logger.debug(
                    f"Created variable {var_name} with domain {min_val}-{max_val} (size: {len(domain)})"
                )

            # Add constraints
            logger.debug("Adding constraints...")
            supported_constraint_count = 0
            unsupported_constraint_count = 0

            for constraint in csp_problem.constraints:
                if constraint.predicate is None:
                    logger.warning(f"Skipping constraint {constraint.name} with no predicate")
                    continue

                try:
                    # Get variables in scope
                    scope_vars = [self.var_map[var] for var in constraint.scope]

                    # Handle different constraint types by name or pattern
                    constraint_name = constraint.name.lower()

                    if "all_different" in constraint_name or "alldiff" in constraint_name:
                        # AllDifferent constraint (most common for Sudoku)
                        model.AddAllDifferent(scope_vars)
                        supported_constraint_count += 1
                        logger.debug(
                            f"Added AllDifferent constraint on {len(scope_vars)} variables"
                        )
                    elif "sum" in constraint_name:
                        # Sum constraint
                        target_sum = constraint.parameters.get("sum", 0)
                        model.Add(sum(scope_vars) == target_sum)
                        supported_constraint_count += 1
                        logger.debug(f"Added Sum constraint (target={target_sum})")
                    else:
                        # Try to use the predicate to generate allowed assignments
                        # This works for small scopes but is expensive for large ones
                        if len(scope_vars) <= 4:
                            # Generate allowed assignments by testing predicate
                            allowed = self._generate_allowed_assignments(
                                constraint, scope_vars, csp_problem
                            )
                            if allowed:
                                model.AddAllowedAssignments(scope_vars, allowed)
                                supported_constraint_count += 1
                                logger.debug(
                                    f"Added constraint {constraint.name} via allowed assignments"
                                )
                            else:
                                logger.warning(
                                    f"Could not generate allowed assignments for {constraint.name}"
                                )
                                unsupported_constraint_count += 1
                        else:
                            # Too large to enumerate - skip
                            logger.warning(
                                f"Constraint {constraint.name} with scope {len(scope_vars)} is too large to enumerate. Skipping."
                            )
                            unsupported_constraint_count += 1

                except Exception as e:
                    logger.error(f"Failed to add constraint {constraint.name}: {e}")
                    unsupported_constraint_count += 1

            logger.info(
                f"OR-Tools model created with {len(self.var_map)} variables, "
                f"{supported_constraint_count} supported constraints, "
                f"{unsupported_constraint_count} unsupported constraints"
            )

            if unsupported_constraint_count > 0:
                logger.warning(
                    f"OR-Tools model has {unsupported_constraint_count} unsupported constraints. "
                    f"Solution may be incomplete. Consider using python-constraint solver."
                )

            return model

        except Exception as e:
            logger.error(f"Failed to build OR-Tools model: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _generate_allowed_assignments(
        self, constraint: Any, scope_vars: List[Any], csp_problem: CSPProblem
    ) -> List[List[int]]:
        """
        Generate allowed assignments for a constraint by testing the predicate.

        This is expensive but works for arbitrary predicates on small scopes.
        """
        try:
            from itertools import product

            # Get domains for all variables in constraint
            domains = []
            for var_name in constraint.scope:
                domain = csp_problem.variables[var_name].domain
                domains.append(domain)

            # Test all combinations
            allowed = []
            for assignment_tuple in product(*domains):
                assignment_dict = {
                    var: val
                    for var, val in zip(constraint.scope, assignment_tuple)
                }
                try:
                    if constraint.predicate(assignment_dict, constraint.parameters):
                        allowed.append(list(assignment_tuple))
                except Exception:
                    # Predicate failed for this assignment - not allowed
                    pass

            return allowed

        except Exception as e:
            logger.error(f"Failed to generate allowed assignments: {e}")
            return []
