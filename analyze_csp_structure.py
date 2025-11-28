#!/usr/bin/env python3
"""Analyze the structure of the CSP being created."""

import json
from pathlib import Path
from src.data.dataset import SudokuDataset
from src.models.qwen_model import QwenVLModel
from src.modules.rule_inference import RuleInferenceModule
from src.modules.state_extraction import StateExtractionModule
from src.modules.csp_translator import CSPTranslator
from src.core.puzzle_state import PuzzleState

def main():
    print("=" * 70)
    print("CSP STRUCTURE ANALYSIS")
    print("=" * 70)

    # Load a puzzle
    dataset_path = Path("data/raw/sudoku/")
    dataset = SudokuDataset(dataset_path)

    if not dataset.solved_examples:
        print("No solved examples found!")
        return

    # Use first solved example for rule inference
    training_examples = dataset.solved_examples[:3]
    print(f"\n[1/4] Using {len(training_examples)} solved examples for rule inference")

    # Initialize VLM
    vlm = QwenVLModel(device="cuda", precision="float16", max_tokens=512)
    vlm.load_model()

    try:
        # Infer rules
        print("\n[2/4] Inferring rules from examples...")
        rule_module = RuleInferenceModule(vlm)
        rules = rule_module.infer_rules(training_examples, validate=True)

        if rules is None:
            print("Failed to infer rules!")
            return

        print(f"\n  Rules inferred:")
        for i, rule in enumerate(rules.rules):
            print(f"    {i+1}. {rule.constraint_type.value} on {len(rule.scope)} variables")
            print(f"       Scope: {rule.scope[:3]}{'...' if len(rule.scope) > 3 else ''}")

        # Create a test state (use first unsolved puzzle)
        print("\n[3/4] Creating puzzle state...")
        test_puzzle = dataset.unsolved_puzzles[0]

        # Extract ground truth initial state
        state = PuzzleState(
            grid_size=(9, 9),
            filled_cells=test_puzzle.initial_state.filled_cells
        )

        print(f"\n  State created:")
        print(f"    Filled cells: {len(state.filled_cells)}")
        print(f"    Empty cells: {len(state.empty_cells)}")

        # Translate to CSP
        print("\n[4/4] Translating to CSP...")
        csp = CSPTranslator.translate(rules, state)

        if csp is None:
            print("Failed to translate to CSP!")
            return

        print(f"\n  CSP Structure:")
        print(f"    Total variables: {len(csp.variables)}")
        print(f"    Total constraints: {len(csp.constraints)}")

        # Analyze variable domains
        domain_sizes = [len(v.domain) for v in csp.variables.values()]
        print(f"\n  Variable Domain Analysis:")
        print(f"    Variables with domain=1 (fixed): {sum(1 for d in domain_sizes if d == 1)}")
        print(f"    Variables with domain=9 (open): {sum(1 for d in domain_sizes if d == 9)}")
        print(f"    Average domain size: {sum(domain_sizes)/len(domain_sizes):.1f}")

        # Analyze constraints
        constraint_sizes = [len(c.scope) for c in csp.constraints]
        print(f"\n  Constraint Analysis:")
        print(f"    Constraints by scope size:")
        for size in sorted(set(constraint_sizes)):
            count = sum(1 for s in constraint_sizes if s == size)
            print(f"      Scope size {size}: {count} constraints")

        # Show first few constraints
        print(f"\n  First 5 constraints:")
        for i, constraint in enumerate(csp.constraints[:5]):
            print(f"    {i+1}. {constraint.name}")
            print(f"       Scope size: {len(constraint.scope)}")
            print(f"       First vars: {constraint.scope[:3]}")

        print(f"\n  CSP Size Summary:")
        print(f"    Total constraint predicate calls: ~{len(csp.constraints) * 100:,}")
        print(f"    Search space (upper bound): 9^{len([v for v in csp.variables.values() if len(v.domain) > 1])}")

        print("\n" + "=" * 70)
        print("ANALYSIS COMPLETE")
        print("=" * 70)

    finally:
        vlm.unload_model()

if __name__ == "__main__":
    main()
