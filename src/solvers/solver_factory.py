"""Factory for creating CSP solvers with configurable backend."""

import logging
from typing import Optional, Dict, Any

from src.core.csp_problem import CSPProblem

logger = logging.getLogger(__name__)


class SolverFactory:
    """
    Factory for creating CSP solvers.

    Supports multiple backends:
    - "constraint": python-constraint (default, slower but more flexible)
    - "ortools": Google OR-Tools (faster for structured problems)
    """

    @staticmethod
    def create_solver(backend: str = "constraint", **kwargs):
        """
        Create a solver with the specified backend.

        Args:
            backend: "constraint" or "ortools" or "auto" (default: "constraint")
            **kwargs: Additional arguments for solver initialization

        Returns:
            Solver instance

        Raises:
            ValueError: If backend is unsupported
            ImportError: If required library is not installed
        """
        if backend == "auto":
            # Auto-select: use python-constraint (more reliable for now)
            # OR-Tools needs more work to handle arbitrary constraints
            logger.info("Using python-constraint solver (reliable, with timeout support)")
            backend = "constraint"

        if backend == "constraint":
            from src.solvers.csp_solver import CSPSolver
            logger.info("Using python-constraint solver (flexible, with thread-based timeout)")
            return CSPSolver(**kwargs)

        if backend == "ortools":
            try:
                from src.solvers.ortools_solver import ORToolsSolver
                logger.info("Using OR-Tools solver (faster, but limited constraint support)")
                return ORToolsSolver(**kwargs)
            except ImportError as e:
                logger.warning(f"OR-Tools not available: {e}. Falling back to python-constraint.")
                return SolverFactory.create_solver(backend="constraint", **kwargs)

        raise ValueError(f"Unknown solver backend: {backend}. Use 'constraint', 'ortools', or 'auto'.")

    @staticmethod
    def solve_fast(csp_problem: CSPProblem, timeout: int = 60) -> Optional[Dict[str, int]]:
        """
        Quick solve using the fastest available solver.

        Args:
            csp_problem: CSP to solve
            timeout: Timeout in seconds

        Returns:
            Solution dict or None
        """
        solver = SolverFactory.create_solver(timeout=timeout)
        return solver.solve(csp_problem)
