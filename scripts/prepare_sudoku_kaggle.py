#!/usr/bin/env python
"""
Prepare Sudoku dataset from Kaggle CSV files.

This script:
1. Reads Sudoku puzzle strings from CSV
2. Converts to grid format
3. Renders as images
4. Generates ground truth JSON metadata

Expected Kaggle dataset structure:
- sudoku.csv with columns: 'puzzle' (puzzle string), 'solution' (solution string)

Puzzle string format: 81-character string where 0 = empty, 1-9 = filled
"""

import argparse
import csv
import json
import random
from pathlib import Path
from typing import List, Tuple, Dict
from PIL import Image, ImageDraw, ImageFont
from tqdm import tqdm
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import init_config, config


def parse_sudoku_string(s: str) -> List[List[int]]:
    """Convert 81-char string to 9x9 grid."""
    grid = []
    for i in range(9):
        row = [int(s[i * 9 + j]) for j in range(9)]
        grid.append(row)
    return grid


def render_sudoku_image(
    puzzle: List[List[int]],
    image_size: int = 448,
    cell_size: int = 48,
) -> Image.Image:
    """Render Sudoku puzzle as image with clean padding."""
    # Create image with padding
    padding = 12
    total_size = image_size + 2 * padding
    img = Image.new("RGB", (total_size, total_size), color="white")
    draw = ImageDraw.Draw(img)

    # Try to use a monospace font
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Courier.dfont", 32)
    except Exception:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 32)
        except Exception:
            font = ImageFont.load_default()

    # Draw grid lines with offset
    grid_end = padding + image_size
    for i in range(10):
        line_width = 2 if i % 3 == 0 else 1
        y = i * cell_size + padding
        draw.line([(padding, y), (grid_end - 1, y)], fill="black", width=line_width)
        x = i * cell_size + padding
        draw.line([(x, padding), (x, grid_end - 1)], fill="black", width=line_width)

    # Draw numbers
    for row in range(9):
        for col in range(9):
            num = puzzle[row][col]
            if num != 0:
                x = col * cell_size + cell_size // 2 + padding
                y = row * cell_size + cell_size // 2 + padding
                draw.text((x, y), str(num), fill="black", font=font, anchor="mm")

    return img


def puzzle_to_initial_state(puzzle: List[List[int]]) -> List[Dict]:
    """Convert puzzle grid to filled cells list."""
    filled = []
    for i in range(9):
        for j in range(9):
            if puzzle[i][j] != 0:
                filled.append({"row": i, "col": j, "value": puzzle[i][j]})
    return filled


def estimate_difficulty(puzzle: List[List[int]]) -> str:
    """Estimate difficulty based on number of clues."""
    clues = sum(1 for row in puzzle for cell in row if cell != 0)
    if clues >= 35:
        return "easy"
    elif clues >= 27:
        return "medium"
    else:
        return "hard"


def prepare_kaggle_sudoku(
    csv_path: Path,
    output_dir: Path = None,
    num_solved: int = 100,
    num_unsolved: int = 200,
    split_ratio: float = 0.33,  # 33% -> solved (training), 67% -> unsolved (test)
) -> None:
    """
    Prepare Sudoku dataset from Kaggle CSV.

    Args:
        csv_path: Path to sudoku.csv from Kaggle
        output_dir: Output directory (defaults to config)
        num_solved: Number of solved examples to extract
        num_unsolved: Number of test puzzles to extract
        split_ratio: Proportion to use as solved examples
    """
    if output_dir is None:
        output_dir = config().data.raw_dir / "sudoku"

    output_dir = Path(output_dir)
    solved_dir = output_dir / "solved"
    unsolved_dir = output_dir / "unsolved"

    solved_dir.mkdir(parents=True, exist_ok=True)
    unsolved_dir.mkdir(parents=True, exist_ok=True)

    print(f"Reading CSV: {csv_path}")

    # Read all puzzles
    puzzles = []
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Handle different column names
            puzzle_col = "puzzle" if "puzzle" in row else "quizzes"
            solution_col = "solution" if "solution" in row else "solutions"
            puzzles.append({
                "puzzle": row[puzzle_col],
                "solution": row[solution_col],
            })

    total = len(puzzles)
    print(f"Found {total} puzzles")

    # Shuffle
    random.shuffle(puzzles)

    # Split
    split_idx = int(total * split_ratio)
    solved_puzzles = puzzles[:split_idx][:num_solved]
    unsolved_puzzles = puzzles[split_idx:][:num_unsolved]

    # Process solved examples
    print(f"\nProcessing {len(solved_puzzles)} solved examples...")
    for i, p in enumerate(tqdm(solved_puzzles)):
        puzzle = parse_sudoku_string(p["puzzle"])
        solution = parse_sudoku_string(p["solution"])

        # Render image
        image = render_sudoku_image(solution)  # Use solution (filled)
        image_path = solved_dir / f"solved_{i+1:03d}.png"
        image.save(image_path)

        # Save metadata
        metadata = {
            "puzzle_id": f"solved_{i+1:03d}",
            "size": [9, 9],
            "initial_state": {
                "filled_cells": puzzle_to_initial_state(solution)
            },
            "solution": {"cells": solution},
            "difficulty": "medium",
        }
        json_path = solved_dir / f"solved_{i+1:03d}.json"
        with open(json_path, "w") as f:
            json.dump(metadata, f, indent=2)

    # Process test puzzles
    print(f"\nProcessing {len(unsolved_puzzles)} test puzzles...")
    for i, p in enumerate(tqdm(unsolved_puzzles)):
        puzzle = parse_sudoku_string(p["puzzle"])
        solution = parse_sudoku_string(p["solution"])

        # Render puzzle image (with empty cells)
        image = render_sudoku_image(puzzle)
        image_path = unsolved_dir / f"unsolved_{i+1:03d}.png"
        image.save(image_path)

        # Save metadata
        difficulty = estimate_difficulty(puzzle)
        metadata = {
            "puzzle_id": f"unsolved_{i+1:03d}",
            "size": [9, 9],
            "initial_state": {
                "filled_cells": puzzle_to_initial_state(puzzle)
            },
            "solution": {"cells": solution},
            "difficulty": difficulty,
        }
        json_path = unsolved_dir / f"unsolved_{i+1:03d}.json"
        with open(json_path, "w") as f:
            json.dump(metadata, f, indent=2)

    print(f"\n✓ Dataset prepared successfully!")
    print(f"  Solved examples: {len(solved_puzzles)} at {solved_dir}")
    print(f"  Test puzzles: {len(unsolved_puzzles)} at {unsolved_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Prepare Sudoku dataset from Kaggle CSV"
    )
    parser.add_argument(
        "csv_path",
        type=Path,
        help="Path to sudoku.csv from Kaggle",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory (default: config.data.raw_dir/sudoku)",
    )
    parser.add_argument(
        "--num-solved",
        type=int,
        default=100,
        help="Number of solved examples to extract",
    )
    parser.add_argument(
        "--num-unsolved",
        type=int,
        default=200,
        help="Number of test puzzles to extract",
    )
    parser.add_argument(
        "--split-ratio",
        type=float,
        default=0.33,
        help="Proportion for solved examples",
    )

    args = parser.parse_args()

    if not args.csv_path.exists():
        print(f"Error: CSV file not found: {args.csv_path}")
        sys.exit(1)

    init_config()
    prepare_kaggle_sudoku(
        csv_path=args.csv_path,
        output_dir=args.output_dir,
        num_solved=args.num_solved,
        num_unsolved=args.num_unsolved,
        split_ratio=args.split_ratio,
    )
