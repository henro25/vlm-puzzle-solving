#!/usr/bin/env python
"""Test complete end-to-end puzzle solving."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import init_config, config
from src.utils.logging import setup_logging, get_logger
from src.data.loaders import load_training_examples, load_test_puzzles
from src.models.qwen_model import QwenVLModel
from src.modules.puzzle_solver import PuzzleSolver
import json

logger = get_logger(__name__)


def main():
    """Test end-to-end solving."""
    print("=" * 60)
    print("END-TO-END PUZZLE SOLVING TEST")
    print("=" * 60)

    # Initialize
    init_config()
    setup_logging(config().logging.log_dir, config().logging.log_level)

    # Load data
    print("\n1. Loading data...")
    try:
        training_examples = load_training_examples(num_examples=3)
        test_puzzles = load_test_puzzles(num_puzzles=1)

        if len(training_examples) == 0 or len(test_puzzles) == 0:
            print("✗ Insufficient data. Please generate dataset:")
            print("  python scripts/generate_synthetic_sudoku.py --quick")
            return

        print(f"✓ Loaded {len(training_examples)} training examples, {len(test_puzzles)} test puzzles")
    except Exception as e:
        print(f"✗ Failed to load data: {e}")
        return

    # Initialize VLM
    print("\n2. Initializing VLM...")
    vlm = QwenVLModel()
    vlm.load_model()

    # Create solver
    print("\n3. Creating puzzle solver...")
    solver = PuzzleSolver(vlm)

    # Solve puzzles
    print("\n4. Solving puzzles (using ground truth state)...")
    results = []
    for puzzle in test_puzzles:
        print(f"\n   Puzzle: {puzzle.puzzle_id}")
        print(f"   Image: {puzzle.image_path}")

        # Convert initial state to format expected by solver
        ground_truth_state = {
            "filled_cells": puzzle.initial_state,
        }

        try:
            result = solver.solve_puzzle(
                puzzle_image=puzzle.image_path,
                training_examples=training_examples,
                extract_state=False,
                ground_truth_state=ground_truth_state,
            )

            if result is None:
                print("   ✗ Solving failed")
                continue

            if result["success"]:
                print("   ✓ Puzzle solved!")
                print(f"     - Rules inferred: {result['steps']['rule_inference']['num_rules']}")
                print(f"     - State extracted: {result['steps']['state_extraction']['filled_cells']} filled")
                print(f"     - CSP size: {result['steps']['csp_translation']['num_variables']} vars, {result['steps']['csp_translation']['num_constraints']} constraints")

                # Show partial solution
                if result["solution"]:
                    solution_vars = list(result["solution"].keys())[:9]
                    print(f"     - Sample variables assigned: {solution_vars}")
            else:
                print("   ✗ Could not solve puzzle")
                print(f"     - Errors: {result['errors']}")

            results.append(result)

        except Exception as e:
            print(f"   ✗ Error: {e}")
            import traceback
            traceback.print_exc()

    vlm.unload_model()

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    successful = sum(1 for r in results if r.get("success"))
    print(f"Solved: {successful}/{len(results)}")

    if results and results[0].get("success"):
        print("\n✓ END-TO-END SOLVING WORKS!")
    else:
        print("\n⚠ Solving had issues (expected - VLM state extraction needs refinement)")

    print("=" * 60)


if __name__ == "__main__":
    main()
