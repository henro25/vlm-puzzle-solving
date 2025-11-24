"""Data structures for representing puzzle state."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import json
from pathlib import Path


@dataclass
class PuzzleState:
    """Represents the state of a puzzle (filled and empty cells)."""

    grid_size: Tuple[int, int] = (9, 9)
    filled_cells: Dict[Tuple[int, int], int] = field(default_factory=dict)
    empty_cells: List[Tuple[int, int]] = field(default_factory=list)
    domains: Dict[Tuple[int, int], List[int]] = field(default_factory=dict)
    confidence: Dict[Tuple[int, int], float] = field(default_factory=dict)

    def __post_init__(self):
        """Validate and initialize state."""
        if not self.empty_cells and not self.filled_cells:
            # Auto-populate empty cells
            rows, cols = self.grid_size
            all_cells = {(i, j) for i in range(rows) for j in range(cols)}
            filled = set(self.filled_cells.keys())
            self.empty_cells = sorted(list(all_cells - filled))

        # Initialize default domains if not provided
        if not self.domains:
            rows, cols = self.grid_size
            for i in range(rows):
                for j in range(cols):
                    if (i, j) not in self.filled_cells:
                        self.domains[(i, j)] = list(range(1, 10))

    def get_cell_value(self, row: int, col: int) -> Optional[int]:
        """Get value at cell, or None if empty."""
        return self.filled_cells.get((row, col))

    def set_cell_value(self, row: int, col: int, value: int) -> None:
        """Set value at cell."""
        self.filled_cells[(row, col)] = value
        if (row, col) in self.empty_cells:
            self.empty_cells.remove((row, col))
        if (row, col) in self.domains:
            self.domains[(row, col)] = [value]

    def get_domain(self, row: int, col: int) -> List[int]:
        """Get possible values for cell."""
        if (row, col) in self.filled_cells:
            return [self.filled_cells[(row, col)]]
        return self.domains.get((row, col), list(range(1, 10)))

    def to_grid(self) -> List[List[Optional[int]]]:
        """Convert to 2D grid representation."""
        rows, cols = self.grid_size
        grid = [[None for _ in range(cols)] for _ in range(rows)]

        for (r, c), value in self.filled_cells.items():
            grid[r][c] = value

        return grid

    def to_dict(self) -> dict:
        """Convert state to dictionary."""
        return {
            "grid_size": self.grid_size,
            "filled_cells": {str(k): v for k, v in self.filled_cells.items()},
            "empty_cells": self.empty_cells,
            "domains": {str(k): v for k, v in self.domains.items()},
            "confidence": {str(k): v for k, v in self.confidence.items()},
        }

    @staticmethod
    def from_dict(data: dict) -> "PuzzleState":
        """Create state from dictionary."""
        filled_cells = {
            tuple(map(int, k.strip("()").split(", "))): v
            for k, v in data.get("filled_cells", {}).items()
        }
        domains = {
            tuple(map(int, k.strip("()").split(", "))): v
            for k, v in data.get("domains", {}).items()
        }
        confidence = {
            tuple(map(int, k.strip("()").split(", "))): v
            for k, v in data.get("confidence", {}).items()
        }

        return PuzzleState(
            grid_size=tuple(data.get("grid_size", (9, 9))),
            filled_cells=filled_cells,
            empty_cells=data.get("empty_cells", []),
            domains=domains,
            confidence=confidence,
        )

    def save(self, path: Path) -> None:
        """Save state to JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @staticmethod
    def load(path: Path) -> "PuzzleState":
        """Load state from JSON file."""
        with open(path, "r") as f:
            data = json.load(f)
        return PuzzleState.from_dict(data)
