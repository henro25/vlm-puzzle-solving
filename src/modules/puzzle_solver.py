"""End-to-end puzzle solving pipeline."""

import logging
from pathlib import Path
from typing import Optional, Dict, Any

from src.models.vlm_interface import VLMInterface
from src.modules.rule_inference import RuleInferenceModule
from src.modules.state_extraction import StateExtractionModule
from src.modules.csp_translator import CSPTranslator
from src.solvers.solver_factory import SolverFactory
from src.data.dataset import SudokuDataset, SudokuPuzzle

logger = logging.getLogger(__name__)


class PuzzleSolver:
    """
    Complete end-to-end pipeline for solving puzzles.

    Pipeline:
    1. Learn constraint rules from solved examples
    2. Extract state from unsolved puzzle
    3. Translate rules + state into CSP
    4. Solve CSP
    5. Return solution
    """

    def __init__(self, vlm: VLMInterface, csp_solver_backend: str = "ortools"):
        """
        Initialize puzzle solver.

        Args:
            vlm: Vision-Language Model interface
            csp_solver_backend: Solver backend ("ortools" or "constraint")
        """
        self.vlm = vlm
        self.rule_module = RuleInferenceModule(vlm)
        self.state_module = StateExtractionModule(vlm)
        self.csp_solver = SolverFactory.create_solver(
            backend=csp_solver_backend, timeout=60
        )

    def solve_puzzle(
        self,
        puzzle_image: Path,
        training_examples: SudokuDataset,
        extract_state: bool = True,
        ground_truth_state: Optional[Dict] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Solve a single puzzle end-to-end.

        Args:
            puzzle_image: Path to unsolved puzzle image
            training_examples: Solved examples for rule learning
            extract_state: Whether to use VLM for state extraction (vs ground truth)
            ground_truth_state: Ground truth initial state (optional, used if extract_state=False)

        Returns:
            Result dict with solution, steps, timing info, or None if fails
        """
        logger.info(f"Solving puzzle: {puzzle_image}")

        result = {
            "puzzle_image": str(puzzle_image),
            "success": False,
            "solution": None,
            "steps": {},
            "errors": [],
        }

        # Step 1: Infer rules
        logger.info("Step 1: Inferring constraint rules...")
        try:
            rules = self.rule_module.infer_rules(list(training_examples), validate=True)
            if rules is None:
                result["errors"].append("Rule inference failed")
                return result

            result["steps"]["rule_inference"] = {
                "num_rules": len(rules.rules),
                "confidence": rules.metadata.get("confidence", 0),
            }
            logger.info(f"  ✓ Inferred {len(rules.rules)} rules")

        except Exception as e:
            result["errors"].append(f"Rule inference error: {e}")
            logger.error(f"Rule inference failed: {e}")
            return result

        # Step 2: Extract state
        logger.info("Step 2: Extracting puzzle state...")
        try:
            if extract_state and ground_truth_state is None:
                state = self.state_module.extract_state(puzzle_image, validate=False)
            elif ground_truth_state is not None:
                # Use ground truth state
                from src.core.puzzle_state import PuzzleState
                state = PuzzleState(
                    grid_size=(9, 9),
                    filled_cells=ground_truth_state.get("filled_cells", {}),
                )
                logger.info("Using ground truth state")
            else:
                result["errors"].append("No state provided and extract_state=False")
                return result

            if state is None:
                result["errors"].append("State extraction failed")
                return result

            result["steps"]["state_extraction"] = {
                "filled_cells": len(state.filled_cells),
                "empty_cells": len(state.empty_cells),
            }
            logger.info(f"  ✓ Extracted state: {len(state.filled_cells)} filled, {len(state.empty_cells)} empty")

        except Exception as e:
            result["errors"].append(f"State extraction error: {e}")
            logger.error(f"State extraction failed: {e}")
            return result

        # Step 3: Translate to CSP
        logger.info("Step 3: Translating to CSP...")
        try:
            csp = CSPTranslator.translate(rules, state)
            if csp is None:
                result["errors"].append("CSP translation failed")
                return result

            result["steps"]["csp_translation"] = {
                "num_variables": len(csp.variables),
                "num_constraints": len(csp.constraints),
            }
            logger.info(f"  ✓ CSP created: {len(csp.variables)} variables, {len(csp.constraints)} constraints")

        except Exception as e:
            result["errors"].append(f"CSP translation error: {e}")
            logger.error(f"CSP translation failed: {e}")
            return result

        # Step 4: Solve
        logger.info("Step 4: Solving CSP...")
        try:
            solution = self.csp_solver.solve(csp)
            if solution is None:
                result["errors"].append("CSP solver found no solution")
                logger.warning("  ✗ No solution found")
                return result

            result["solution"] = solution
            result["steps"]["csp_solving"] = {
                "num_variables_assigned": len(solution),
            }
            logger.info(f"  ✓ Solution found: {len(solution)} variables assigned")
            result["success"] = True

        except Exception as e:
            result["errors"].append(f"CSP solving error: {e}")
            logger.error(f"CSP solving failed: {e}")
            return result

        logger.info("✓ Puzzle solved successfully!")
        return result

    def __enter__(self):
        """Context manager entry."""
        self.vlm.load_model()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.vlm.unload_model()
