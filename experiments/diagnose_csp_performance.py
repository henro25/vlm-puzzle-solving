#!/usr/bin/env python
"""Diagnose CSP solver performance bottlenecks."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import init_config, config
from src.utils.logging import setup_logging, get_logger
from src.data.loaders import load_training_examples, load_test_puzzles
from src.models.qwen_model import QwenVLModel
from src.modules.puzzle_solver import PuzzleSolver
from src.modules.rule_inference import RuleInferenceModule
from src.modules.state_extraction import StateExtractionModule
from src.modules.csp_translator import CSPTranslator
from src.solvers.csp_solver import CSPSolver
import json

logger = get_logger(__name__)


def diagnose():
    """Diagnose each phase of the pipeline."""
    print("=" * 60)
    print("CSP PERFORMANCE DIAGNOSTICS")
    print("=" * 60)

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

        print(f"✓ Loaded {len(training_examples)} training examples, {len(test_puzzles)} test puzzles")
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
        # Phase 1: Rule Inference
        print("\n3. Rule Inference...")
        rule_module = RuleInferenceModule(vlm)
        start = time.time()
        rules = rule_module.infer_rules(list(training_examples), validate=True)
        rule_time = time.time() - start
        print(f"✓ Inferred {len(rules.rules)} rules in {rule_time:.2f}s")
        print(f"  Rules: {[r.constraint_type.value for r in rules.rules]}")

        # Phase 2: State Extraction (use ground truth)
        print("\n4. State Extraction (ground truth)...")
        from src.core.puzzle_state import PuzzleState
        state = PuzzleState(
            grid_size=(9, 9),
            filled_cells=ground_truth_state.get("filled_cells", {}),
        )
        print(f"✓ State created: {len(state.filled_cells)} filled, {len(state.empty_cells)} empty")

        # Phase 3: CSP Translation
        print("\n5. CSP Translation...")
        start = time.time()
        csp = CSPTranslator.translate(rules, state)
        translate_time = time.time() - start
        print(f"✓ CSP created in {translate_time:.2f}s")
        print(f"  Variables: {len(csp.variables)}")
        print(f"  Constraints: {len(csp.constraints)}")

        # Analyze CSP structure
        print("\n  CSP Structure Analysis:")
        domain_sizes = [len(var.domain) for var in csp.variables.values()]
        print(f"  - Avg domain size: {sum(domain_sizes) / len(domain_sizes):.1f}")
        print(f"  - Min domain size: {min(domain_sizes)}")
        print(f"  - Max domain size: {max(domain_sizes)}")
        print(f"  - Variables with domain=1: {sum(1 for d in domain_sizes if d == 1)}")
        print(f"  - Variables with domain=9: {sum(1 for d in domain_sizes if d == 9)}")

        constraint_sizes = [len(c.scope) for c in csp.constraints]
        print(f"  - Avg constraint size: {sum(constraint_sizes) / len(constraint_sizes):.1f}")
        print(f"  - Min constraint size: {min(constraint_sizes)}")
        print(f"  - Max constraint size: {max(constraint_sizes)}")

        # Phase 4: CSP Solving
        print("\n6. CSP Solving...")
        csp_solver = CSPSolver(timeout=10)  # 10 second timeout for diagnostics

        start = time.time()
        solution = csp_solver.solve(csp)
        solve_time = time.time() - start

        if solution:
            print(f"✓ Solution found in {solve_time:.2f}s")
            print(f"  Variables assigned: {len(solution)}")
        else:
            print(f"✗ No solution found in {solve_time:.2f}s (timeout?)")

        # Summary
        print("\n" + "=" * 60)
        print("TIMING SUMMARY")
        print("=" * 60)
        print(f"Rule Inference: {rule_time:.2f}s")
        print(f"CSP Translation: {translate_time:.2f}s")
        print(f"CSP Solving: {solve_time:.2f}s")
        print(f"TOTAL: {rule_time + translate_time + solve_time:.2f}s")

        if solve_time > 1.0:
            print(f"\n⚠ Slow solving detected! ({solve_time:.2f}s)")
            print("  Consider optimizations:")
            print("  1. Better variable ordering heuristics (MRV, LCV)")
            print("  2. Constraint reordering (most constraining first)")
            print("  3. Arc consistency preprocessing")
            print("  4. Switch to faster solver (OR-Tools, MiniZinc)")

    finally:
        vlm.unload_model()
        print("\n" + "=" * 60)


if __name__ == "__main__":
    diagnose()
