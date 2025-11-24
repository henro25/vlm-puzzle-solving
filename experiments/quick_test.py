#!/usr/bin/env python
"""Quick sanity test of system components."""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import init_config, setup_logging, config
from src.data.dataset import SudokuDataset
from src.utils.image_processing import load_image
from src.core.puzzle_state import PuzzleState
from src.core.constraint_rules import ConstraintRuleSet, ConstraintRule, ConstraintType


def test_config():
    """Test configuration system."""
    print("✓ Testing configuration...")
    cfg = config()
    assert cfg.vlm.model_name == "Qwen/Qwen2-VL-7B-Instruct"
    assert cfg.device in ["cuda", "cpu"]
    print(f"  - VLM: {cfg.vlm.model_name}")
    print(f"  - Device: {cfg.device}")
    print(f"  - Data dir: {cfg.data.data_dir}")


def test_puzzle_state():
    """Test PuzzleState data structure."""
    print("\n✓ Testing PuzzleState...")

    state = PuzzleState(
        grid_size=(9, 9),
        filled_cells={(0, 0): 5, (0, 1): 3, (0, 2): 4},
    )

    assert len(state.filled_cells) == 3
    assert state.get_cell_value(0, 0) == 5
    assert state.get_cell_value(0, 3) is None
    assert (0, 3) in state.empty_cells

    # Test grid conversion
    grid = state.to_grid()
    assert grid[0][0] == 5
    assert grid[0][3] is None

    print(f"  - Filled cells: {len(state.filled_cells)}")
    print(f"  - Empty cells: {len(state.empty_cells)}")


def test_constraint_rules():
    """Test ConstraintRuleSet data structure."""
    print("\n✓ Testing ConstraintRuleSet...")

    rules = ConstraintRuleSet()

    # Add variables
    rules.add_variable("row_0", list(range(1, 10)), "First row of Sudoku")
    rules.add_variable("col_0", list(range(1, 10)), "First column of Sudoku")

    # Add constraint
    rule = ConstraintRule(
        constraint_type=ConstraintType.ALL_DIFFERENT,
        scope=["row_0"],
        description="All values in row 0 must be different"
    )
    rules.add_rule(rule)

    assert len(rules.variables) == 2
    assert len(rules.rules) == 1
    assert len(rules.get_rules_for_variable("row_0")) == 1

    print(f"  - Variables: {len(rules.variables)}")
    print(f"  - Rules: {len(rules.rules)}")
    print(f"  - Rules for 'row_0': {len(rules.get_rules_for_variable('row_0'))}")


def test_dataset():
    """Test Dataset loading."""
    print("\n✓ Testing Dataset...")

    cfg = config()
    dataset = SudokuDataset(cfg.data.raw_dir / "sudoku")

    # Add a test puzzle
    dataset.add_puzzle(
        puzzle_id="test_001",
        image_path=Path("test.png"),
        initial_state={(0, 0): 5},
        solution=[[5, 3, 4, 6, 7, 8, 9, 1, 2]] + [[0] * 9 for _ in range(8)],
    )

    assert len(dataset) == 1
    assert dataset.get_by_id("test_001") is not None

    print(f"  - Dataset size: {len(dataset)}")
    print(f"  - Can retrieve by ID: {dataset.get_by_id('test_001').puzzle_id}")


def main():
    """Run all tests."""
    print("=" * 60)
    print("QUICK SANITY TEST")
    print("=" * 60)

    # Initialize
    init_config()
    setup_logging(config().logging.log_dir, config().logging.log_level)

    try:
        test_config()
        test_puzzle_state()
        test_constraint_rules()
        test_dataset()

        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Generate dataset: python scripts/generate_synthetic_sudoku.py --quick")
        print("2. Test VLM: python -c 'from src.models.qwen_model import QwenVLModel; print(QwenVLModel())'")
        print("3. Run full experiments: python -m experiments.run_main_experiment")

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
