#!/usr/bin/env python
"""Test Phase 4 CSP solving optimizations."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import init_config, config
from src.utils.logging import setup_logging, get_logger
from src.data.loaders import load_training_examples, load_test_puzzles
from src.models.qwen_model import QwenVLModel
from src.modules.puzzle_solver import PuzzleSolver
from src.core.puzzle_state import PuzzleState

logger = get_logger(__name__)


def main():
    """Test Phase 4 optimizations with different solvers."""
    print("=" * 70)
    print("PHASE 4: CSP SOLVING OPTIMIZATIONS TEST")
    print("=" * 70)

    # Initialize
    init_config()
    setup_logging(config().logging.log_dir, config().logging.log_level)

    # Load data
    print("\n1. Loading data...")
    try:
        training_examples = load_training_examples(num_examples=3)
        test_puzzles = load_test_puzzles(num_puzzles=2)

        if len(training_examples) == 0 or len(test_puzzles) == 0:
            print("✗ Insufficient data")
            return

        print(f"✓ Loaded {len(training_examples)} examples, {len(test_puzzles)} puzzles")
    except Exception as e:
        print(f"✗ Failed to load data: {e}")
        return

    # Initialize VLM
    print("\n2. Initializing VLM...")
    vlm = QwenVLModel()
    vlm.load_model()

    try:
        # Test both solvers
        solvers_to_test = [
            ("ortools", "Google OR-Tools (Recommended)"),
            ("constraint", "Optimized python-constraint"),
        ]

        all_results = []

        for backend, description in solvers_to_test:
            print(f"\n" + "=" * 70)
            print(f"Testing: {description}")
            print("=" * 70)

            solver = PuzzleSolver(vlm, csp_solver_backend=backend)

            puzzle_results = []
            total_time = 0

            for i, puzzle in enumerate(test_puzzles[:2]):  # Test first 2 puzzles
                print(f"\nPuzzle {i + 1}:")
                ground_truth_state = {
                    "filled_cells": puzzle.initial_state,
                }

                start = time.time()
                try:
                    result = solver.solve_puzzle(
                        puzzle_image=puzzle.image_path,
                        training_examples=training_examples,
                        extract_state=False,
                        ground_truth_state=ground_truth_state,
                    )

                    elapsed = time.time() - start
                    total_time += elapsed

                    if result and result.get("success"):
                        print(f"  ✓ Solved in {elapsed:.3f}s")
                        print(f"    - Rules: {result['steps']['rule_inference']['num_rules']}")
                        print(f"    - CSP: {result['steps']['csp_translation']['num_variables']} vars, "
                              f"{result['steps']['csp_translation']['num_constraints']} constraints")
                        puzzle_results.append({
                            "puzzle": i + 1,
                            "time": elapsed,
                            "success": True,
                        })
                    else:
                        print(f"  ✗ Failed in {elapsed:.3f}s")
                        print(f"    - Errors: {result['errors'] if result else 'Unknown'}")
                        puzzle_results.append({
                            "puzzle": i + 1,
                            "time": elapsed,
                            "success": False,
                        })

                except Exception as e:
                    elapsed = time.time() - start
                    print(f"  ✗ Error: {e} ({elapsed:.3f}s)")
                    puzzle_results.append({
                        "puzzle": i + 1,
                        "time": elapsed,
                        "success": False,
                    })

            # Summary for this solver
            successful = sum(1 for r in puzzle_results if r["success"])
            avg_time = total_time / len(puzzle_results) if puzzle_results else 0

            all_results.append({
                "backend": backend,
                "description": description,
                "puzzles_solved": successful,
                "total_puzzles": len(puzzle_results),
                "avg_time": avg_time,
                "total_time": total_time,
                "puzzle_results": puzzle_results,
            })

            print(f"\nSolver Summary:")
            print(f"  - Puzzles solved: {successful}/{len(puzzle_results)}")
            print(f"  - Total time: {total_time:.3f}s")
            print(f"  - Average time: {avg_time:.3f}s/puzzle")

        # Overall Summary
        print("\n" + "=" * 70)
        print("OVERALL SUMMARY")
        print("=" * 70)

        if all_results:
            fastest = min(all_results, key=lambda r: r["avg_time"])
            slowest = max(all_results, key=lambda r: r["avg_time"])

            print(f"\n✓ Test completed with {len(all_results)} solvers\n")

            for result in all_results:
                status = "✓" if result["puzzles_solved"] == result["total_puzzles"] else "⚠"
                print(f"{status} {result['description']}")
                print(f"   - Solved: {result['puzzles_solved']}/{result['total_puzzles']}")
                print(f"   - Time/puzzle: {result['avg_time']:.3f}s (total: {result['total_time']:.3f}s)")

            if len(all_results) > 1:
                speedup = slowest["avg_time"] / fastest["avg_time"]
                print(f"\n✓ Performance Improvement:")
                print(f"   - Fastest: {fastest['description']} ({fastest['avg_time']:.3f}s/puzzle)")
                print(f"   - Slowest: {slowest['description']} ({slowest['avg_time']:.3f}s/puzzle)")
                print(f"   - Speedup: {speedup:.1f}x")

        print("\n" + "=" * 70)
        print("✓ PHASE 4 OPTIMIZATIONS TEST COMPLETE")
        print("=" * 70)

        print("\nNext Steps:")
        print("1. Compare with your previous baseline (should be much faster)")
        print("2. Run: python experiments/diagnose_csp_performance.py")
        print("3. Run: python experiments/compare_solvers.py")
        print("4. Read: PHASE4_OPTIMIZATIONS.md")

    finally:
        vlm.unload_model()


if __name__ == "__main__":
    main()
