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

    def __init__(self, vlm: VLMInterface, csp_solver_backend: str = "constraint"):
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
        import time
        logger.info(f"Solving puzzle: {puzzle_image}")
        print(f"  [TIMING] Starting puzzle solve at {time.strftime('%H:%M:%S')}")

        result = {
            "puzzle_image": str(puzzle_image),
            "success": False,
            "solution": None,
            "steps": {},
            "errors": [],
        }

        # Step 1: Infer rules
        logger.info("Step 1: Inferring constraint rules...")
        print(f"  [TIMING] Starting rule inference at {time.strftime('%H:%M:%S')}", flush=True)
        try:
            print(f"  [TIMING] About to call infer_rules...", flush=True)
            rules = self.rule_module.infer_rules(list(training_examples), validate=True)
            print(f"  [TIMING] infer_rules returned", flush=True)
            if rules is None:
                result["errors"].append("Rule inference failed")
                return result

            result["steps"]["rule_inference"] = {
                "num_rules": len(rules.rules),
                "confidence": rules.metadata.get("confidence", 0),
            }
            print(f"  [TIMING] Rule inference done at {time.strftime('%H:%M:%S')}", flush=True)
            logger.info(f"  ✓ Inferred {len(rules.rules)} rules")

        except Exception as e:
            result["errors"].append(f"Rule inference error: {e}")
            logger.error(f"Rule inference failed: {e}")
            return result

        print(f"  [TIMING] Past rule inference exception block at {time.strftime('%H:%M:%S')}", flush=True)

        # Step 2: Extract state
        logger.info("Step 2: Extracting puzzle state...")
        print(f"  [TIMING] Starting state extraction at {time.strftime('%H:%M:%S')}", flush=True)
        try:
            print(f"  [TIMING] extract_state={extract_state}, ground_truth_state={ground_truth_state is not None}", flush=True)
            if extract_state and ground_truth_state is None:
                print(f"  [TIMING] Calling state_module.extract_state...", flush=True)
                state = self.state_module.extract_state(puzzle_image, validate=False)
                print(f"  [TIMING] state_module.extract_state returned", flush=True)
            elif ground_truth_state is not None:
                # Use ground truth state
                print(f"  [TIMING] Using ground truth state", flush=True)
                from src.core.puzzle_state import PuzzleState
                state = PuzzleState(
                    grid_size=(9, 9),
                    filled_cells=ground_truth_state.get("filled_cells", {}),
                )
                logger.info("Using ground truth state")
                print(f"  [TIMING] PuzzleState created", flush=True)
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
            print(f"  [TIMING] State extraction done at {time.strftime('%H:%M:%S')}", flush=True)
            logger.info(f"  ✓ Extracted state: {len(state.filled_cells)} filled, {len(state.empty_cells)} empty")

        except Exception as e:
            result["errors"].append(f"State extraction error: {e}")
            logger.error(f"State extraction failed: {e}")
            import traceback
            traceback.print_exc()
            return result

        # Step 3: Translate to CSP
        logger.info("Step 3: Translating to CSP...")
        print(f"  [TIMING] Starting CSP translation at {time.strftime('%H:%M:%S')}")
        try:
            csp = CSPTranslator.translate(rules, state)
            if csp is None:
                result["errors"].append("CSP translation failed")
                return result

            result["steps"]["csp_translation"] = {
                "num_variables": len(csp.variables),
                "num_constraints": len(csp.constraints),
            }
            print(f"  [TIMING] CSP translation done at {time.strftime('%H:%M:%S')}")
            logger.info(f"  ✓ CSP created: {len(csp.variables)} variables, {len(csp.constraints)} constraints")

        except Exception as e:
            result["errors"].append(f"CSP translation error: {e}")
            logger.error(f"CSP translation failed: {e}")
            return result

        # Step 4: Solve
        logger.info("Step 4: Solving CSP...")
        print(f"  [TIMING] Starting CSP solving at {time.strftime('%H:%M:%S')}")
        try:
            solution = self.csp_solver.solve(csp)
            if solution is None:
                result["errors"].append("CSP solver found no solution")
                print(f"  [TIMING] CSP solving failed at {time.strftime('%H:%M:%S')}")
                logger.warning("  ✗ No solution found")
                return result

            result["solution"] = solution
            result["steps"]["csp_solving"] = {
                "num_variables_assigned": len(solution),
            }
            print(f"  [TIMING] CSP solving done at {time.strftime('%H:%M:%S')}")
            logger.info(f"  ✓ Solution found: {len(solution)} variables assigned")
            result["success"] = True

        except Exception as e:
            result["errors"].append(f"CSP solving error: {e}")
            logger.error(f"CSP solving failed: {e}")
            return result

        print(f"  [TIMING] Puzzle solved at {time.strftime('%H:%M:%S')}")
        logger.info("✓ Puzzle solved successfully!")
        return result

    def __enter__(self):
        """Context manager entry."""
        self.vlm.load_model()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.vlm.unload_model()
