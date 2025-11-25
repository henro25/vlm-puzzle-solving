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

            status = solver.Solve(model)
            elapsed = time.time() - start_time

            if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                logger.warning(f"No solution found (status: {status}, time: {elapsed:.2f}s)")
                return None

            # Extract solution
            solution = {}
            for var_name, cp_var in self.var_map.items():
                solution[var_name] = solver.Value(cp_var)

            logger.info(f"Solution found in {elapsed:.2f}s (status: {status})")
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
                if len(domain) == 1:
                    # Fixed variable
                    cp_var = model.NewIntVar(domain[0], domain[0], var_name)
                else:
                    # Variable with domain
                    cp_var = model.NewIntVar(min(domain), max(domain), var_name)
                    # Add element constraint if domain is not contiguous
                    if max(domain) - min(domain) + 1 != len(domain):
                        model.AddElement(
                            cp_var, domain, cp_model.NewConstant(0)
                        )

                self.var_map[var_name] = cp_var
                logger.debug(
                    f"Created variable {var_name} with domain {domain}"
                )

            # Add constraints
            logger.debug("Adding constraints...")
            for constraint in csp_problem.constraints:
                if constraint.predicate is None:
                    logger.warning(f"Skipping constraint {constraint.name} with no predicate")
                    continue

                try:
                    # Get variables in scope
                    scope_vars = [self.var_map[var] for var in constraint.scope]

                    # Handle different constraint types
                    if constraint.name.startswith("all_different"):
                        # AllDifferent constraint
                        model.AddAllDifferent(scope_vars)
                        logger.debug(
                            f"Added AllDifferent constraint on {len(scope_vars)} variables"
                        )
                    elif constraint.name.startswith("sum"):
                        # Sum constraint
                        target_sum = constraint.parameters.get("sum", 0)
                        model.Add(sum(scope_vars) == target_sum)
                        logger.debug(f"Added Sum constraint (target={target_sum})")
                    else:
                        # Generic constraint: try to handle with callback
                        # For now, skip unsupported constraint types
                        logger.warning(f"Skipping constraint {constraint.name} (not directly supported)")

                except Exception as e:
                    logger.error(f"Failed to add constraint {constraint.name}: {e}")

            logger.info(f"OR-Tools model created with {len(self.var_map)} variables")
            return model

        except Exception as e:
            logger.error(f"Failed to build OR-Tools model: {e}")
            import traceback
            traceback.print_exc()
            return None
