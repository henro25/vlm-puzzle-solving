#!/usr/bin/env python
"""Test end-to-end with detailed progress output."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import init_config, config
from src.utils.logging import setup_logging, get_logger
from src.data.loaders import load_training_examples, load_test_puzzles
from src.models.qwen_model import QwenVLModel
from src.modules.puzzle_solver import PuzzleSolver

logger = get_logger(__name__)


def main():
    """Test end-to-end solving with verbose output."""
    print("=" * 70)
    print("END-TO-END PUZZLE SOLVING TEST (VERBOSE)")
    print("=" * 70)

    # Initialize
    print("\n[1/5] Initializing config...")
    init_config()
    setup_logging(config().logging.log_dir, config().logging.log_level)

    # Load data
    print("[2/5] Loading data...")
    try:
        training_examples = load_training_examples(num_examples=3)
        test_puzzles = load_test_puzzles(num_puzzles=1)

        if len(training_examples) == 0 or len(test_puzzles) == 0:
            print("✗ Insufficient data")
            return

        print(f"  ✓ Loaded {len(training_examples)} training examples, {len(test_puzzles)} test puzzles")
    except Exception as e:
        print(f"✗ Failed to load data: {e}")
        return

    # Initialize VLM
    print("\n[3/5] Initializing VLM...")
    vlm = QwenVLModel()

    start_load = time.time()
    vlm.load_model()
    load_time = time.time() - start_load
    print(f"  ✓ Model loaded in {load_time:.1f}s")

    # Create solver
    print("\n[4/5] Creating puzzle solver...")
    solver = PuzzleSolver(vlm)
    print(f"  ✓ Solver initialized (backend: constraint)")

    # Solve puzzles
    print("\n[5/5] Solving puzzles (using ground truth state)...")
    results = []

    for puzzle in test_puzzles:
        print(f"\n  Puzzle: {puzzle.puzzle_id}")
        print(f"  Image: {puzzle.image_path}")

        # Convert initial state to format expected by solver
        ground_truth_state = {
            "filled_cells": puzzle.initial_state,
        }

        start_solve = time.time()
        try:
            print(f"    → Calling solver...")
            result = solver.solve_puzzle(
                puzzle_image=puzzle.image_path,
                training_examples=training_examples,
                extract_state=False,
                ground_truth_state=ground_truth_state,
            )
            solve_time = time.time() - start_solve

            if result is None:
                print(f"    ✗ Solving failed (None returned)")
                continue

            if result["success"]:
                print(f"    ✓ Puzzle solved in {solve_time:.2f}s!")
                print(f"      - Rules inferred: {result['steps']['rule_inference']['num_rules']}")
                print(f"      - State extracted: {result['steps']['state_extraction']['filled_cells']} filled")
                print(f"      - CSP size: {result['steps']['csp_translation']['num_variables']} vars, {result['steps']['csp_translation']['num_constraints']} constraints")
                print(f"      - Solution: {result['steps']['csp_solving']['num_variables_assigned']} variables assigned")

                # Show partial solution
                if result["solution"]:
                    solution_vars = list(result["solution"].keys())[:5]
                    values = [result["solution"][v] for v in solution_vars]
                    print(f"      - Sample solution: {dict(zip(solution_vars, values))}")
            else:
                print(f"    ✗ Could not solve puzzle in {solve_time:.2f}s")
                print(f"      - Errors: {result['errors']}")

            results.append(result)

        except Exception as e:
            solve_time = time.time() - start_solve
            print(f"    ✗ Error after {solve_time:.2f}s: {e}")
            import traceback
            traceback.print_exc()

    vlm.unload_model()

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    successful = sum(1 for r in results if r.get("success"))
    print(f"Solved: {successful}/{len(results)}")

    if results and results[0].get("success"):
        print("\n✓ END-TO-END SOLVING WORKS!")
    else:
        print("\n⚠ Solving had issues")
        if results:
            print(f"First puzzle errors: {results[0].get('errors', ['Unknown'])}")

    print("=" * 70)


if __name__ == "__main__":
    main()
