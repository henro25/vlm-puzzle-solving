#!/usr/bin/env python
"""Generate synthetic Sudoku puzzles and render them as images."""

import argparse
import json
import random
from pathlib import Path
from typing import List, Tuple, Dict, Any
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from tqdm import tqdm
import sys
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import init_config, config

# Sudoku generator
class SudokuGenerator:
    """Generate valid Sudoku puzzles."""

    def __init__(self, seed: int = None):
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

    @staticmethod
    def is_valid(grid: List[List[int]], row: int, col: int, num: int) -> bool:
        """Check if placing num at (row, col) is valid."""
        # Check row
        if num in grid[row]:
            return False

        # Check column
        if num in [grid[i][col] for i in range(9)]:
            return False

        # Check 3x3 box
        box_row, box_col = 3 * (row // 3), 3 * (col // 3)
        for i in range(box_row, box_row + 3):
            for j in range(box_col, box_col + 3):
                if grid[i][j] == num:
                    return False

        return True

    def generate_solution(self) -> List[List[int]]:
        """Generate a valid Sudoku solution."""
        grid = [[0] * 9 for _ in range(9)]

        def fill_grid(grid):
            for row in range(9):
                for col in range(9):
                    if grid[row][col] == 0:
                        nums = list(range(1, 10))
                        random.shuffle(nums)
                        for num in nums:
                            if self.is_valid(grid, row, col, num):
                                grid[row][col] = num
                                if fill_grid(grid):
                                    return True
                                grid[row][col] = 0
                        return False
            return True

        fill_grid(grid)
        return grid

    def generate_puzzle(self, difficulty: str = "medium") -> Tuple[List[List[int]], List[List[int]]]:
        """Generate puzzle with solution."""
        solution = self.generate_solution()
        puzzle = [row[:] for row in solution]

        # Remove cells based on difficulty
        if difficulty == "easy":
            to_remove = random.randint(35, 40)
        elif difficulty == "medium":
            to_remove = random.randint(41, 46)
        else:  # hard
            to_remove = random.randint(47, 52)

        cells = [(i, j) for i in range(9) for j in range(9)]
        random.shuffle(cells)

        for i, j in cells[:to_remove]:
            puzzle[i][j] = 0

        return puzzle, solution


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
        # Horizontal
        y = i * cell_size + padding
        draw.line([(padding, y), (grid_end - 1, y)], fill="black", width=line_width)
        # Vertical
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


def puzzle_to_initial_state(puzzle: List[List[int]]) -> Dict[Tuple[int, int], int]:
    """Convert puzzle grid to initial state dict."""
    initial_state = {}
    for i in range(9):
        for j in range(9):
            if puzzle[i][j] != 0:
                initial_state[(i, j)] = puzzle[i][j]
    return initial_state


def generate_dataset(
    num_solved: int = 100,
    num_unsolved: int = 200,
    output_dir: Path = None,
    quick: bool = False,
) -> None:
    """Generate complete Sudoku dataset."""
    if output_dir is None:
        output_dir = config().data.raw_dir / "sudoku"

    output_dir = Path(output_dir)
    solved_dir = output_dir / "solved"
    unsolved_dir = output_dir / "unsolved"

    solved_dir.mkdir(parents=True, exist_ok=True)
    unsolved_dir.mkdir(parents=True, exist_ok=True)

    generator = SudokuGenerator(seed=42)

    print(f"Generating {num_solved} solved examples...")
    for i in tqdm(range(num_solved)):
        puzzle, solution = generator.generate_puzzle("medium")

        # Render as image
        image = render_sudoku_image(puzzle)
        image_path = solved_dir / f"solved_{i+1:03d}.png"
        image.save(image_path)

        # Save metadata
        metadata = {
            "puzzle_id": f"solved_{i+1:03d}",
            "size": [9, 9],
            "initial_state": {
                "filled_cells": [
                    {"row": r, "col": c, "value": solution[r][c]}
                    for r in range(9)
                    for c in range(9)
                ]
            },
            "solution": {
                "cells": solution,
            },
            "difficulty": "medium",
        }
        json_path = solved_dir / f"solved_{i+1:03d}.json"
        with open(json_path, "w") as f:
            json.dump(metadata, f, indent=2)

    print(f"Generating {num_unsolved} test puzzles...")
    for i in tqdm(range(num_unsolved)):
        difficulty = random.choice(["easy", "medium", "hard"])
        puzzle, solution = generator.generate_puzzle(difficulty)

        # Render as image
        image = render_sudoku_image(puzzle)
        image_path = unsolved_dir / f"unsolved_{i+1:03d}.png"
        image.save(image_path)

        # Save metadata with both initial state and solution
        initial_state = puzzle_to_initial_state(puzzle)
        metadata = {
            "puzzle_id": f"unsolved_{i+1:03d}",
            "size": [9, 9],
            "initial_state": {
                "filled_cells": [
                    {"row": r, "col": c, "value": v}
                    for (r, c), v in initial_state.items()
                ]
            },
            "solution": {
                "cells": solution,
            },
            "difficulty": difficulty,
        }
        json_path = unsolved_dir / f"unsolved_{i+1:03d}.json"
        with open(json_path, "w") as f:
            json.dump(metadata, f, indent=2)

    print(f"\n✓ Dataset generated successfully!")
    print(f"  Solved examples: {solved_dir}")
    print(f"  Test puzzles: {unsolved_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic Sudoku dataset")
    parser.add_argument("--num-solved", type=int, default=100, help="Number of solved examples")
    parser.add_argument("--num-unsolved", type=int, default=200, help="Number of test puzzles")
    parser.add_argument("--output-dir", type=Path, default=None, help="Output directory")
    parser.add_argument("--quick", action="store_true", help="Quick mode (5 puzzles)")

    args = parser.parse_args()

    if args.quick:
        args.num_solved = 5
        args.num_unsolved = 5

    init_config()
    generate_dataset(
        num_solved=args.num_solved,
        num_unsolved=args.num_unsolved,
        output_dir=args.output_dir,
        quick=args.quick,
    )
