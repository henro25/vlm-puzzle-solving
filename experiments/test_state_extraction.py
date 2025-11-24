#!/usr/bin/env python
"""Test state extraction module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import init_config, config
from src.utils.logging import setup_logging, get_logger
from src.data.loaders import load_test_puzzles
from src.models.qwen_model import QwenVLModel
from src.modules.state_extraction import StateExtractionModule
from src.parsers.state_parser import StateParser

logger = get_logger(__name__)


def main():
    """Test state extraction."""
    print("=" * 60)
    print("STATE EXTRACTION TEST")
    print("=" * 60)

    # Initialize
    init_config()
    setup_logging(config().logging.log_dir, config().logging.log_level)

    # Load test puzzles
    print("\n1. Loading test puzzles...")
    try:
        dataset = load_test_puzzles(num_puzzles=2)
        if len(dataset) == 0:
            print("✗ No test puzzles found. Please generate dataset first:")
            print("  python scripts/generate_synthetic_sudoku.py --quick")
            return
        print(f"✓ Loaded {len(dataset)} puzzles")
    except Exception as e:
        print(f"✗ Failed to load puzzles: {e}")
        return

    # Initialize VLM
    print("\n2. Initializing VLM...")
    vlm = QwenVLModel()
    vlm.load_model()

    # Create state extraction module
    print("\n3. Extracting puzzle states...")
    try:
        extraction_module = StateExtractionModule(vlm)

        for idx, puzzle in enumerate(dataset):
            print(f"\n   Puzzle #{idx + 1}: {puzzle.puzzle_id}")
            print(f"   Image: {puzzle.image_path}")

            # Extract state
            state = extraction_module.extract_state(
                puzzle.image_path,
                validate=True,
                auto_correct=False,
            )

            if state is None:
                print(f"   ✗ Extraction failed")
                continue

            print(f"   ✓ Extracted state")
            print(f"     - Filled cells: {len(state.filled_cells)}")
            print(f"     - Empty cells: {len(state.empty_cells)}")

            # Validate
            report = StateParser.validate_state(state)
            if report["valid"]:
                print(f"   ✓ Validation passed")
            else:
                print(f"   ⚠ Validation issues: {report['issues']}")

            # Show sample grid
            grid = state.to_grid()
            print("\n   Extracted Grid (first 3 rows):")
            for row_idx in range(min(3, len(grid))):
                row_str = " ".join(str(v) if v else "." for v in grid[row_idx])
                print(f"     Row {row_idx}: {row_str}")

    except Exception as e:
        print(f"✗ State extraction failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        vlm.unload_model()

    print("\n" + "=" * 60)
    print("✓ TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
