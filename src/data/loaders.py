"""Data loaders for puzzle datasets."""

from pathlib import Path
from typing import Optional, List
import logging

from src.data.dataset import SudokuDataset
from src.config import config

logger = logging.getLogger(__name__)


def load_sudoku_dataset(
    dataset_dir: Optional[Path] = None,
    split: str = "all",  # "train", "test", or "all"
) -> SudokuDataset:
    """
    Load Sudoku dataset from disk.

    Args:
        dataset_dir: Directory containing puzzle data (defaults to config)
        split: Which split to load

    Returns:
        SudokuDataset instance
    """
    if dataset_dir is None:
        dataset_dir = config().data.raw_dir / "sudoku"

    dataset_dir = Path(dataset_dir)

    if split == "train":
        puzzle_dir = dataset_dir / "solved"
    elif split == "test":
        puzzle_dir = dataset_dir / "unsolved"
    elif split == "all":
        puzzle_dir = dataset_dir
    else:
        raise ValueError(f"Unknown split: {split}")

    logger.info(f"Loading Sudoku dataset from {puzzle_dir}")

    dataset = SudokuDataset(puzzle_dir)
    dataset.load_from_directory(puzzle_dir)

    logger.info(f"Loaded {len(dataset)} puzzles")

    return dataset


def load_training_examples(
    num_examples: Optional[int] = None,
) -> SudokuDataset:
    """
    Load solved Sudoku examples for rule inference training.

    Args:
        num_examples: Number of examples to load (default: config)

    Returns:
        SudokuDataset with solved examples
    """
    if num_examples is None:
        num_examples = config().data.num_train_examples

    dataset = load_sudoku_dataset(split="train")

    if len(dataset) > num_examples:
        # Randomly sample if more available
        import random
        random.seed(config().seed)
        indices = random.sample(range(len(dataset)), num_examples)
        sampled = SudokuDataset(dataset.base_dir)
        sampled.puzzles = [dataset.puzzles[i] for i in sorted(indices)]
        dataset = sampled

    logger.info(f"Loaded {len(dataset)} training examples")
    return dataset


def load_test_puzzles(
    num_puzzles: Optional[int] = None,
    difficulty_filter: Optional[List[str]] = None,
) -> SudokuDataset:
    """
    Load test Sudoku puzzles.

    Args:
        num_puzzles: Number of puzzles to load (default: config)
        difficulty_filter: Filter by difficulty level

    Returns:
        SudokuDataset with test puzzles
    """
    if num_puzzles is None:
        num_puzzles = config().data.num_test_puzzles

    dataset = load_sudoku_dataset(split="test")

    # Filter by difficulty if specified
    if difficulty_filter:
        filtered = SudokuDataset(dataset.base_dir)
        filtered.puzzles = [p for p in dataset.puzzles if p.difficulty in difficulty_filter]
        dataset = filtered

    # Sample if needed
    if len(dataset) > num_puzzles:
        import random
        random.seed(config().seed)
        indices = random.sample(range(len(dataset)), num_puzzles)
        sampled = SudokuDataset(dataset.base_dir)
        sampled.puzzles = [dataset.puzzles[i] for i in sorted(indices)]
        dataset = sampled

    logger.info(f"Loaded {len(dataset)} test puzzles")
    return dataset
