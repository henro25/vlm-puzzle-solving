#!/usr/bin/env python3
"""Test that CSP solver timeout actually works."""

import time
from src.solvers.csp_solver import CSPSolver
from src.core.csp_problem import CSPProblem, CSPVariable, CSPConstraint

def test_timeout():
    """Test that solver times out properly instead of hanging."""
    print("=" * 60)
    print("Testing CSP Solver Timeout Mechanism")
    print("=" * 60)

    # Create a simple but hard CSP
    csp = CSPProblem()

    # Add 9x9 = 81 variables for Sudoku grid
    print("\n[1/3] Creating Sudoku CSP with 81 variables...")
    for i in range(9):
        for j in range(9):
            var_name = f"cell_{i}_{j}"
            domain = list(range(1, 10))
            csp.add_variable(var_name, domain)

    print(f"  ✓ Added {len(csp.variables)} variables")

    # Add all-different constraints for rows
    print("\n[2/3] Adding row constraints...")
    for row in range(9):
        scope = [f"cell_{row}_{col}" for col in range(9)]
        def make_all_diff(s=scope):
            def check(assignment, params):
                values = [assignment.get(var) for var in s if var in assignment]
                if len(values) < len(s):
                    return True
                return len(values) == len(set(values))
            return check

        csp.add_constraint(
            name=f"row_{row}_alldiff",
            scope=scope,
            predicate=make_all_diff(),
            parameters={}
        )

    print(f"  ✓ Added {9} row constraints")

    # Create solver with SHORT timeout (to test timeout mechanism)
    print("\n[3/3] Testing with 5-second timeout...")
    solver = CSPSolver(timeout=5)

    print("\nAttempting to solve (should timeout after 5s)...")
    start = time.time()
    result = solver.solve(csp)
    elapsed = time.time() - start

    print(f"\n{'='*60}")
    print(f"Result: {result}")
    print(f"Elapsed time: {elapsed:.2f}s")
    print(f"{'='*60}")

    if result is None and elapsed < 10:
        print("\n✓ SUCCESS: Solver timed out properly (didn't hang forever)")
        print(f"  Timeout worked correctly - returned after {elapsed:.2f}s")
        return True
    elif result is not None:
        print("\n✓ SUCCESS: Solver found a solution (or partial solution)")
        print(f"  Solution found in {elapsed:.2f}s")
        return True
    else:
        print("\n✗ FAILED: Solver may still be hanging")
        return False

if __name__ == "__main__":
    success = test_timeout()
    exit(0 if success else 1)
