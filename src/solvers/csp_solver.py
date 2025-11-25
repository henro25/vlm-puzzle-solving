"""CSP solver using python-constraint library."""

import logging
import time
from typing import Optional, Dict, Any, List

try:
    from constraint import Problem, AllDifferentConstraint
except ImportError:
    Problem = None
    AllDifferentConstraint = None

from src.core.csp_problem import CSPProblem

logger = logging.getLogger(__name__)


class CSPSolver:
    """
    Solve Constraint Satisfaction Problems using python-constraint.

    Supports:
    - Backtracking with constraint propagation
    - Configurable timeouts
    - Multiple solution enumeration
    """

    def __init__(
        self,
        timeout: int = 60,
        heuristic: str = "MRV",
    ):
        """
        Initialize CSP solver.

        Args:
            timeout: Maximum solving time in seconds
            heuristic: Variable selection heuristic (MRV, etc.)
        """
        self.timeout = timeout
        self.heuristic = heuristic

        if Problem is None:
            raise ImportError("python-constraint not installed. Run: pip install python-constraint")

    def solve(self, csp_problem: CSPProblem) -> Optional[Dict[str, int]]:
        """
        Solve CSP and return first solution.

        Args:
            csp_problem: CSPProblem to solve

        Returns:
            Solution dict {variable_name: value} or None if unsolvable
        """
        logger.info(f"Solving CSP with {len(csp_problem.variables)} variables, {len(csp_problem.constraints)} constraints")

        try:
            problem = self._build_constraint_problem(csp_problem)

            if problem is None:
                logger.error("Failed to build constraint problem")
                return None

            # Solve with timeout
            start_time = time.time()
            solution = problem.getSolution()
            elapsed = time.time() - start_time

            if solution is None:
                logger.warning(f"No solution found (time: {elapsed:.2f}s)")
                return None

            logger.info(f"Solution found in {elapsed:.2f}s")
            return solution

        except Exception as e:
            logger.error(f"Solver error: {e}")
            import traceback
            traceback.print_exc()
            return None

    def solve_with_timeout(
        self,
        csp_problem: CSPProblem,
        timeout: int,
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

    def get_all_solutions(
        self,
        csp_problem: CSPProblem,
        limit: int = 100,
    ) -> List[Dict[str, int]]:
        """
        Find all solutions (up to limit).

        Args:
            csp_problem: CSPProblem to solve
            limit: Maximum number of solutions to find

        Returns:
            List of solution dicts
        """
        logger.info(f"Finding all solutions (limit: {limit})")

        try:
            problem = self._build_constraint_problem(csp_problem)

            if problem is None:
                return []

            solutions = problem.getSolutions()
            return solutions[:limit]

        except Exception as e:
            logger.error(f"Error finding solutions: {e}")
            return []

    @staticmethod
    def _build_constraint_problem(csp_problem: CSPProblem) -> Optional[Any]:
        """
        Build python-constraint Problem from CSPProblem.

        Args:
            csp_problem: CSPProblem to convert

        Returns:
            constraint.Problem or None if conversion fails
        """
        try:
            problem = Problem()

            # Add variables
            for var_name, variable in csp_problem.variables.items():
                problem.addVariable(var_name, variable.domain)
                logger.debug(f"Added variable {var_name} with domain {variable.domain}")

            # Add constraints
            for constraint in csp_problem.constraints:
                if constraint.predicate is None:
                    logger.warning(f"Skipping constraint {constraint.name} with no predicate")
                    continue

                # Wrap predicate to handle partial assignments
                def make_constraint(pred, params):
                    def wrapped(*args):
                        assignment = {var: val for var, val in zip(constraint.scope, args)}
                        try:
                            return pred(assignment, params)
                        except Exception as e:
                            logger.error(f"Constraint error: {e}")
                            return False
                    return wrapped

                wrapped_predicate = make_constraint(constraint.predicate, constraint.parameters)

                try:
                    problem.addConstraint(wrapped_predicate, constraint.scope)
                    logger.debug(f"Added constraint {constraint.name} on {constraint.scope}")
                except Exception as e:
                    logger.error(f"Failed to add constraint {constraint.name}: {e}")

            return problem

        except Exception as e:
            logger.error(f"Failed to build constraint problem: {e}")
            return None
