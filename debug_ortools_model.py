#!/usr/bin/env python3
"""Debug why OR-Tools model is invalid."""

import logging
from pathlib import Path
from src.data.dataset import SudokuDataset
from src.models.qwen_model import QwenVLModel
from src.modules.rule_inference import RuleInferenceModule
from src.modules.csp_translator import CSPTranslator
from src.core.puzzle_state import PuzzleState

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def main():
    print("=" * 70)
    print("DEBUGGING OR-TOOLS MODEL VALIDITY")
    print("=" * 70)

    # Load dataset
    dataset_path = Path("data/raw/sudoku/")
    dataset = SudokuDataset(dataset_path)

    if not dataset.solved_examples or not dataset.unsolved_puzzles:
        print("No puzzles found!")
        return

    # Infer rules
    print("\n[1/4] Loading VLM and inferring rules...")
    vlm = QwenVLModel(device="cuda", precision="float16", max_tokens=512)
    vlm.load_model()

    try:
        rule_module = RuleInferenceModule(vlm)
        rules = rule_module.infer_rules(dataset.solved_examples[:1], validate=True)

        if rules is None:
            print("Failed to infer rules!")
            return

        print(f"✓ Inferred {len(rules.rules)} rules:")
        for i, rule in enumerate(rules.rules):
            print(f"  {i+1}. {rule.constraint_type.value}")
            print(f"     Scope: {rule.scope}")
            print(f"     Parameters: {rule.parameters}")

        # Create state
        print("\n[2/4] Creating puzzle state...")
        test_puzzle = dataset.unsolved_puzzles[0]
        state = PuzzleState(
            grid_size=(9, 9),
            filled_cells=test_puzzle.initial_state.filled_cells
        )
        print(f"✓ State: {len(state.filled_cells)} filled, {len(state.empty_cells)} empty")

        # Translate to CSP
        print("\n[3/4] Translating to CSP...")
        csp = CSPTranslator.translate(rules, state)

        if csp is None:
            print("Failed to translate CSP!")
            return

        print(f"✓ CSP: {len(csp.variables)} variables, {len(csp.constraints)} constraints")

        # Now try to build OR-Tools model
        print("\n[4/4] Building OR-Tools model...")
        try:
            from ortools.sat.python import cp_model
            from src.solvers.ortools_solver import ORToolsSolver

            solver = ORToolsSolver(timeout=60)
            model = solver._build_ortools_model(csp)

            if model is None:
                print("✗ Model building failed!")
                return

            print("✓ Model built successfully!")

            # Try to validate model
            print("\nValidating model...")
            cp_solver = cp_model.CpSolver()
            status = cp_solver.Solve(model)

            status_names = {
                0: "OPTIMAL",
                1: "FEASIBLE",
                2: "INFEASIBLE",
                3: "MODEL_INVALID",
            }
            status_name = status_names.get(status, f"UNKNOWN({status})")

            print(f"Status: {status_name}")

            if status == 3:  # MODEL_INVALID
                print("\n✗ MODEL IS INVALID!")
                print("\nPossible causes:")
                print("1. Constraint scope contains non-existent variables")
                print("2. Constraint has negative or invalid domain")
                print("3. Unsupported constraint types")
                print("4. Invalid allowed assignments")

                # Try to find the problem
                print("\nDebugging CSP structure:")
                print(f"  Variables: {len(csp.variables)}")
                print(f"  Constraints: {len(csp.constraints)}")

                # Check variable domains
                print("\n  Variable domain analysis:")
                for i, (name, var) in enumerate(list(csp.variables.items())[:5]):
                    print(f"    {name}: domain={var.domain}")

                # Check constraints
                print("\n  First 3 constraints:")
                for i, constraint in enumerate(csp.constraints[:3]):
                    print(f"    {i+1}. {constraint.name}")
                    print(f"       Scope: {constraint.scope}")
                    print(f"       Scope length: {len(constraint.scope)}")

                    # Check if all scope variables exist
                    missing = [v for v in constraint.scope if v not in csp.variables]
                    if missing:
                        print(f"       ✗ MISSING VARIABLES: {missing}")
                    else:
                        print(f"       ✓ All variables exist")

            elif status == 2:  # INFEASIBLE
                print("\n✗ PUZZLE IS UNSOLVABLE!")
                print("The CSP has no valid solution (contradictory constraints)")

            elif status == 0 or status == 1:  # OPTIMAL or FEASIBLE
                print("\n✓ MODEL IS VALID AND HAS A SOLUTION!")
                if status == 0:
                    print("  Status: Optimal solution found")
                else:
                    print("  Status: Feasible solution found")

        except Exception as e:
            print(f"✗ Error building/validating model: {e}")
            import traceback
            traceback.print_exc()

    finally:
        vlm.unload_model()

if __name__ == "__main__":
    main()
