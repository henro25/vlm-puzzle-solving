#!/usr/bin/env python
"""Compare performance of different CSP solvers."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import init_config, config
from src.utils.logging import setup_logging, get_logger
from src.data.loaders import load_training_examples, load_test_puzzles
from src.models.qwen_model import QwenVLModel
from src.modules.rule_inference import RuleInferenceModule
from src.modules.csp_translator import CSPTranslator
from src.core.puzzle_state import PuzzleState
from src.solvers.solver_factory import SolverFactory
import json

logger = get_logger(__name__)


def main():
    """Compare solvers."""
    print("=" * 70)
    print("CSP SOLVER COMPARISON")
    print("=" * 70)

    # Initialize
    init_config()
    setup_logging(config().logging.log_dir, config().logging.log_level)

    # Load data
    print("\n1. Loading data...")
    try:
        training_examples = load_training_examples(num_examples=1)
        test_puzzles = load_test_puzzles(num_puzzles=1)

        if len(training_examples) == 0 or len(test_puzzles) == 0:
            print("✗ Insufficient data. Please generate dataset.")
            return

        print(f"✓ Loaded data")
    except Exception as e:
        print(f"✗ Failed to load data: {e}")
        return

    # Initialize VLM
    print("\n2. Initializing VLM...")
    vlm = QwenVLModel()
    vlm.load_model()

    puzzle = test_puzzles[0]
    ground_truth_state = {
        "filled_cells": puzzle.initial_state,
    }

    try:
        # Rule Inference
        print("\n3. Inferring rules...")
        rule_module = RuleInferenceModule(vlm)
        rules = rule_module.infer_rules(list(training_examples), validate=True)
        print(f"✓ Inferred {len(rules.rules)} rules")

        # State Extraction
        print("\n4. Creating puzzle state...")
        state = PuzzleState(
            grid_size=(9, 9),
            filled_cells=ground_truth_state.get("filled_cells", {}),
        )
        print(f"✓ State: {len(state.filled_cells)} filled, {len(state.empty_cells)} empty")

        # CSP Translation
        print("\n5. Translating to CSP...")
        csp = CSPTranslator.translate(rules, state)
        print(f"✓ CSP: {len(csp.variables)} variables, {len(csp.constraints)} constraints")

        # Solver Comparison
        print("\n" + "=" * 70)
        print("SOLVER PERFORMANCE COMPARISON")
        print("=" * 70)

        solvers = [
            ("constraint", "python-constraint (reference)"),
            ("ortools", "Google OR-Tools (optimized)"),
        ]

        results = []

        for backend, description in solvers:
            print(f"\n{description}...")
            try:
                solver = SolverFactory.create_solver(backend=backend, timeout=30)

                start = time.time()
                solution = solver.solve(csp)
                elapsed = time.time() - start

                if solution:
                    status = "✓ SOLVED"
                    result_status = True
                else:
                    status = "✗ NO SOLUTION"
                    result_status = False

                print(f"  {status} in {elapsed:.3f}s")

                results.append({
                    "solver": backend,
                    "description": description,
                    "time": elapsed,
                    "solved": result_status,
                })

                if solution:
                    print(f"  Variables assigned: {len(solution)}")

            except Exception as e:
                print(f"  ✗ ERROR: {e}")
                results.append({
                    "solver": backend,
                    "description": description,
                    "time": None,
                    "solved": False,
                    "error": str(e),
                })

        # Summary
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)

        successful = [r for r in results if r["solved"]]
        if successful:
            fastest = min(successful, key=lambda r: r["time"])
            print(f"✓ {len(successful)}/{len(results)} solvers found solution")
            print(f"✓ Fastest: {fastest['description']} ({fastest['time']:.3f}s)")

            # Calculate speedup
            if len(successful) > 1:
                times = [r["time"] for r in successful]
                slowest_time = max(times)
                fastest_time = min(times)
                speedup = slowest_time / fastest_time
                print(f"✓ Speedup: {speedup:.1f}x faster with best solver")
        else:
            print("✗ No solver found a solution")

        print("\nDetailed Results:")
        for r in results:
            status = "✓" if r["solved"] else "✗"
            time_str = f"{r['time']:.3f}s" if r["time"] is not None else "ERROR"
            print(f"  {status} {r['description']}: {time_str}")

        print("\n" + "=" * 70)

    finally:
        vlm.unload_model()


if __name__ == "__main__":
    main()
