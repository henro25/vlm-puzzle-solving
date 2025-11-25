#!/usr/bin/env python
"""Debug CSP structure to understand solving failures."""

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

logger = get_logger(__name__)


def main():
    """Debug CSP structure."""
    print("=" * 70)
    print("CSP STRUCTURE DEBUG")
    print("=" * 70)

    # Initialize
    init_config()
    setup_logging(config().logging.log_dir, config().logging.log_level)

    # Load data
    print("\n1. Loading data...")
    try:
        training_examples = load_training_examples(num_examples=3)
        test_puzzles = load_test_puzzles(num_puzzles=1)

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
        puzzle = test_puzzles[0]
        ground_truth_state = {
            "filled_cells": puzzle.initial_state,
        }

        # Phase 1: Rule Inference
        print("\n3. Rule Inference...")
        rule_module = RuleInferenceModule(vlm)
        rules = rule_module.infer_rules(list(training_examples), validate=True)
        print(f"✓ Inferred {len(rules.rules)} rules")

        for i, rule in enumerate(rules.rules):
            print(f"\n  Rule {i+1}: {rule.constraint_type.value}")
            print(f"    - Scope: {rule.scope}")
            print(f"    - Parameters: {rule.parameters}")

        # Phase 2: State Creation
        print("\n4. Creating puzzle state...")
        state = PuzzleState(
            grid_size=(9, 9),
            filled_cells=ground_truth_state.get("filled_cells", {}),
        )
        print(f"✓ State: {len(state.filled_cells)} filled, {len(state.empty_cells)} empty")

        # Phase 3: CSP Translation
        print("\n5. Translating to CSP...")
        csp = CSPTranslator.translate(rules, state)
        print(f"✓ CSP created")

        print(f"\n6. CSP Structure Analysis:")
        print(f"\n  Variables ({len(csp.variables)} total):")

        # Sample variables
        var_list = list(csp.variables.items())
        print(f"    - First 5 variables:")
        for var_name, var in var_list[:5]:
            print(f"      {var_name}: domain = {var.domain}")

        if len(var_list) > 10:
            print(f"    - Last 5 variables:")
            for var_name, var in var_list[-5:]:
                print(f"      {var_name}: domain = {var.domain}")

        # Domain analysis
        domain_sizes = [len(var.domain) for var in csp.variables.values()]
        print(f"\n  Domain Analysis:")
        print(f"    - Min domain size: {min(domain_sizes)}")
        print(f"    - Max domain size: {max(domain_sizes)}")
        print(f"    - Avg domain size: {sum(domain_sizes) / len(domain_sizes):.1f}")
        print(f"    - Fixed variables (domain=1): {sum(1 for d in domain_sizes if d == 1)}")
        print(f"    - Full domain (domain=9): {sum(1 for d in domain_sizes if d == 9)}")

        print(f"\n  Constraints ({len(csp.constraints)} total):")

        # Constraint analysis
        constraint_types = {}
        for constraint in csp.constraints:
            ctype = constraint.name.split("_")[0]
            if ctype not in constraint_types:
                constraint_types[ctype] = []
            constraint_types[ctype].append(constraint)

        for ctype, constraints_of_type in constraint_types.items():
            print(f"    - {ctype}: {len(constraints_of_type)} constraints")
            if constraints_of_type:
                sample = constraints_of_type[0]
                print(f"      Example: {sample.name}")
                print(f"      Scope size: {len(sample.scope)}")
                print(f"      Predicate: {'Yes' if sample.predicate else 'No'}")

        # Constraint scope analysis
        scope_sizes = [len(c.scope) for c in csp.constraints]
        print(f"\n  Constraint Scope Analysis:")
        print(f"    - Min scope size: {min(scope_sizes)}")
        print(f"    - Max scope size: {max(scope_sizes)}")
        print(f"    - Avg scope size: {sum(scope_sizes) / len(scope_sizes):.1f}")

        # Try solving with python-constraint
        print("\n7. Testing with python-constraint solver...")
        from src.solvers.csp_solver import CSPSolver

        start = time.time()
        csp_solver = CSPSolver(timeout=5)
        solution = csp_solver.solve(csp)
        elapsed = time.time() - start

        if solution:
            print(f"✓ Solution found in {elapsed:.3f}s")
            print(f"  Variables assigned: {len(solution)}")
        else:
            print(f"✗ No solution found in {elapsed:.3f}s")

        # Try solving with OR-Tools
        print("\n8. Testing with OR-Tools solver...")
        try:
            from src.solvers.ortools_solver import ORToolsSolver

            start = time.time()
            ortools_solver = ORToolsSolver(timeout=5)
            solution = ortools_solver.solve(csp)
            elapsed = time.time() - start

            if solution:
                print(f"✓ Solution found in {elapsed:.3f}s")
                print(f"  Variables assigned: {len(solution)}")
            else:
                print(f"✗ No solution found in {elapsed:.3f}s")
        except Exception as e:
            print(f"✗ OR-Tools error: {e}")

    finally:
        vlm.unload_model()
        print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
