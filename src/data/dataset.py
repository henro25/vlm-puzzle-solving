"""Dataset classes for puzzle data."""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class SudokuPuzzle:
    """Representation of a single Sudoku puzzle."""

    puzzle_id: str
    image_path: Path
    initial_state: Dict[Tuple[int, int], int]  # Filled cells
    solution: List[List[int]]  # 9x9 solution grid
    difficulty: str = "medium"
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class SudokuDataset:
    """Dataset manager for Sudoku puzzles."""

    def __init__(self, base_dir: Path):
        """
        Initialize dataset.

        Args:
            base_dir: Base directory containing puzzle data
        """
        self.base_dir = Path(base_dir)
        self.puzzles: List[SudokuPuzzle] = []

    def add_puzzle(
        self,
        puzzle_id: str,
        image_path: Path,
        initial_state: Dict[Tuple[int, int], int],
        solution: List[List[int]],
        difficulty: str = "medium",
    ) -> None:
        """Add a puzzle to the dataset."""
        puzzle = SudokuPuzzle(
            puzzle_id=puzzle_id,
            image_path=Path(image_path),
            initial_state=initial_state,
            solution=solution,
            difficulty=difficulty,
        )
        self.puzzles.append(puzzle)

    def load_from_directory(self, puzzle_dir: Path) -> None:
        """
        Load puzzles from directory structure.

        Expected structure:
        puzzle_dir/
        ├── puzzle_001.png
        ├── puzzle_001.json
        ├── puzzle_002.png
        ├── puzzle_002.json
        └── ...
        """
        puzzle_dir = Path(puzzle_dir)
        if not puzzle_dir.exists():
            logger.warning(f"Puzzle directory not found: {puzzle_dir}")
            return

        # Find all JSON metadata files
        json_files = sorted(puzzle_dir.glob("*.json"))

        for json_file in json_files:
            try:
                with open(json_file, "r") as f:
                    data = json.load(f)

                # Find corresponding image
                image_path = puzzle_dir / f"{json_file.stem}.png"
                if not image_path.exists():
                    logger.warning(f"Image not found for {json_file.stem}")
                    continue

                # Parse initial state
                initial_state = {}
                if "initial_state" in data:
                    filled = data["initial_state"].get("filled_cells", [])
                    for cell in filled:
                        initial_state[(cell["row"], cell["col"])] = cell["value"]

                # Parse solution
                solution = data.get("solution", {}).get("cells", [])

                # Add to dataset
                self.add_puzzle(
                    puzzle_id=json_file.stem,
                    image_path=image_path,
                    initial_state=initial_state,
                    solution=solution,
                    difficulty=data.get("difficulty", "medium"),
                )

                logger.debug(f"Loaded puzzle: {json_file.stem}")

            except Exception as e:
                logger.error(f"Failed to load puzzle {json_file}: {e}")

    def split_by_difficulty(
        self, difficulties: Optional[List[str]] = None
    ) -> Dict[str, List[SudokuPuzzle]]:
        """
        Split dataset by difficulty level.

        Args:
            difficulties: List of difficulty levels to filter (default: all)

        Returns:
            Dictionary mapping difficulty → list of puzzles
        """
        if difficulties is None:
            difficulties = ["easy", "medium", "hard"]

        splits = {d: [] for d in difficulties}
        for puzzle in self.puzzles:
            if puzzle.difficulty in splits:
                splits[puzzle.difficulty].append(puzzle)

        return splits

    def get_by_id(self, puzzle_id: str) -> Optional[SudokuPuzzle]:
        """Get puzzle by ID."""
        for puzzle in self.puzzles:
            if puzzle.puzzle_id == puzzle_id:
                return puzzle
        return None

    def __len__(self) -> int:
        """Get number of puzzles in dataset."""
        return len(self.puzzles)

    def __getitem__(self, index: int) -> SudokuPuzzle:
        """Get puzzle by index."""
        return self.puzzles[index]

    def __iter__(self):
        """Iterate over puzzles."""
        return iter(self.puzzles)
