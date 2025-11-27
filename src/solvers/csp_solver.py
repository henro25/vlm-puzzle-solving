"""CSP solver using python-constraint library."""

import logging
import time
import threading
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
        import sys
        logger.info(f"Solving CSP with {len(csp_problem.variables)} variables, {len(csp_problem.constraints)} constraints")
        print(f"  [csp_solver] Building constraint problem...", flush=True)

        try:
            start_build = time.time()
            problem = self._build_constraint_problem(csp_problem)
            build_time = time.time() - start_build
            print(f"  [csp_solver] Built in {build_time:.2f}s", flush=True)

            if problem is None:
                logger.error("Failed to build constraint problem")
                return None

            # Solve with timeout using threading
            print(f"  [csp_solver] Starting solve (timeout={self.timeout}s)...", flush=True)
            start_time = time.time()

            # Use thread-based timeout to enforce actual timeout
            solution_container = {"solution": None}
            error_container = {"error": None}

            def solve_worker():
                try:
                    solution_container["solution"] = problem.getSolution()
                except Exception as e:
                    error_container["error"] = e

            solver_thread = threading.Thread(target=solve_worker, daemon=True)
            solver_thread.start()
            solver_thread.join(timeout=self.timeout)

            elapsed = time.time() - start_time

            if solver_thread.is_alive():
                # Timeout occurred
                logger.warning(f"Solver timeout after {self.timeout}s")
                print(f"  [csp_solver] Timeout after {self.timeout:.2f}s", flush=True)
                return None

            if error_container["error"] is not None:
                logger.error(f"Solver error: {error_container['error']}")
                print(f"  [csp_solver] Error: {error_container['error']}", flush=True)
                return None

            print(f"  [csp_solver] Solve completed in {elapsed:.2f}s", flush=True)

            solution = solution_container["solution"]
            if solution is None:
                logger.warning(f"No solution found (time: {elapsed:.2f}s)")
                print(f"  [csp_solver] No solution found", flush=True)
                return None

            logger.info(f"Solution found in {elapsed:.2f}s")
            print(f"  [csp_solver] Solution found!", flush=True)
            return solution

        except Exception as e:
            logger.error(f"Solver error: {e}")
            print(f"  [csp_solver] Error: {e}", flush=True)
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

            # Optimization 1: Variable ordering (domain size heuristic)
            # Add variables in order of domain size (smallest first)
            # This prioritizes variables with fewer choices, improving pruning
            sorted_vars = sorted(
                csp_problem.variables.items(),
                key=lambda x: len(x[1].domain),
            )

            for var_name, variable in sorted_vars:
                problem.addVariable(var_name, variable.domain)
                if len(variable.domain) == 1:
                    logger.debug(f"Added assigned variable {var_name} = {variable.domain[0]}")
                else:
                    logger.debug(f"Added variable {var_name} with domain size {len(variable.domain)}")

            logger.debug(f"Variable order: domains {[len(csp_problem.variables[v[0]].domain) for v in sorted_vars[:5]]} (first 5)")

            # Optimization 2: Constraint ordering (most constraining first)
            # Add constraints that constrain more variables first
            # This provides better pruning early in search
            sorted_constraints = sorted(
                csp_problem.constraints,
                key=lambda c: len(c.scope),
                reverse=True,
            )

            constraint_count = 0
            for constraint in sorted_constraints:
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
                    constraint_count += 1
                    logger.debug(f"Added constraint {constraint.name} on {len(constraint.scope)} variables")
                except Exception as e:
                    logger.error(f"Failed to add constraint {constraint.name}: {e}")

            logger.info(f"Added {constraint_count}/{len(csp_problem.constraints)} constraints")

            return problem

        except Exception as e:
            logger.error(f"Failed to build constraint problem: {e}")
            return None
