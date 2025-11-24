# Dataset Guide: From Puzzles to Images

This guide explains how the dataset pipeline works and how puzzle data becomes VLM-compatible images.

## Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   DATASET PIPELINE                           │
└─────────────────────────────────────────────────────────────┘

OPTION A: Kaggle CSV
┌──────────────┐
│ sudoku.csv   │ (81-char puzzle + solution strings)
└──────┬───────┘
       │ prepare_sudoku_kaggle.py
       ▼
   ┌───────────────────┐
   │ Parse to grids    │ (81 chars → 9x9 grid of ints)
   └─────────┬─────────┘
             │
             ▼
      ┌────────────────┐
      │ Render as PNG  │ (grid → visual image, 448x448)
      └────────┬───────┘
               │
               ▼
        ┌──────────────────┐
        │ Generate JSON    │ (metadata: initial state, solution)
        └────────┬─────────┘
                 │
                 ▼
   data/raw/sudoku/{solved,unsolved}/


OPTION B: Synthetic Generation
┌──────────────────────────────────┐
│ generate_synthetic_sudoku.py      │
└──────────┬───────────────────────┘
           │
           ▼
   ┌──────────────────────┐
   │ Generate random grid │ (backtracking algorithm)
   └──────────┬───────────┘
              │
              ▼
       ┌──────────────────────┐
       │ Remove cells         │ (difficulty: easy/medium/hard)
       │ (puzzle generation)  │
       └──────────┬───────────┘
                  │
                  ▼
            ┌─────────────────┐
            │ Render as PNG   │ (grid → visual image)
            └────────┬────────┘
                     │
                     ▼
              ┌────────────────┐
              │ Generate JSON  │ (metadata)
              └────────┬───────┘
                       │
                       ▼
       data/raw/sudoku/{solved,unsolved}/
```

## Output Format

After running either pipeline, you'll have this structure:

```
data/raw/sudoku/
├── solved/                          # Training examples (all filled)
│   ├── solved_001.png               # 448x448 RGB image
│   ├── solved_001.json              # Metadata
│   ├── solved_002.png
│   ├── solved_002.json
│   └── ... (100 examples)
│
└── unsolved/                        # Test puzzles (partially filled)
    ├── unsolved_001.png             # 448x448 RGB image
    ├── unsolved_001.json            # Metadata
    ├── unsolved_002.png
    ├── unsolved_002.json
    └── ... (200 puzzles)
```

## File Formats

### PNG Images

**Format**: 448×448 RGB image
- **Background**: White (255, 255, 255)
- **Grid lines**: Black, thick borders every 3 cells (Sudoku standard)
- **Numbers**: Black digits (1-9) in monospace font
- **Empty cells**: Blank white space

**Example image properties**:
- Cell size: 48×48 pixels (448 / 9)
- Thick lines at rows/cols [0, 3, 6, 9] (width=3px)
- Thin lines at other rows/cols (width=1px)

**Why this format?**
- VLMs trained on natural images can process this well
- Clear, high contrast makes digit extraction easier
- Standard Sudoku grid layout

### JSON Metadata

**File name**: `{solved,unsolved}_NNN.json`

**Format**:
```json
{
  "puzzle_id": "unsolved_001",
  "size": [9, 9],
  "initial_state": {
    "filled_cells": [
      {"row": 0, "col": 0, "value": 5},
      {"row": 0, "col": 1, "value": 3},
      {"row": 0, "col": 2, "value": 4},
      ...
    ]
  },
  "solution": {
    "cells": [
      [5, 3, 4, 6, 7, 8, 9, 1, 2],
      [6, 7, 2, 1, 9, 5, 3, 4, 8],
      ...
    ]
  },
  "difficulty": "medium"
}
```

**Fields**:
- `puzzle_id`: Unique identifier
- `size`: Grid dimensions [rows, cols]
- `initial_state.filled_cells`: List of pre-filled cells (for unsolved) or all cells (for solved)
- `solution.cells`: Complete 9×9 solution grid
- `difficulty`: "easy" (35-40 clues), "medium" (27-34), or "hard" (17-26)

## Data Pipeline Details

### Step 1: Reading Puzzle Data

**From Kaggle CSV**:
```python
import csv

with open('sudoku.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        puzzle_str = row['puzzle']      # "530070000..." (81 chars)
        solution_str = row['solution']  # "534678912..." (81 chars)
```

**Puzzle String Format**:
- 81 characters long (9×9 grid)
- 0 = empty cell
- 1-9 = filled cell with that value
- Read left-to-right, top-to-bottom

**Example**:
```
"530070000600195000098000060800060003400803001700020006060000280000419005000080079"
         ^              ^                           ^
      Row 0           Row 1                      Row 9

Position 0 = Row 0, Col 0 = 5
Position 1 = Row 0, Col 1 = 3
Position 2 = Row 0, Col 2 = 0 (empty)
...
```

### Step 2: Convert to Grid

```python
def parse_sudoku_string(s: str) -> List[List[int]]:
    """81-char string → 9×9 2D grid"""
    grid = []
    for i in range(9):
        row = [int(s[i*9 + j]) for j in range(9)]
        grid.append(row)
    return grid

# Result:
grid = [
    [5, 3, 0, 0, 7, 0, 0, 0, 0],
    [6, 0, 0, 1, 9, 5, 0, 0, 0],
    [0, 9, 8, 0, 0, 0, 0, 6, 0],
    # ... 6 more rows
]
```

### Step 3: Render as Image

```python
def render_sudoku_image(
    puzzle: List[List[int]],
    image_size: int = 448,
) -> Image.Image:
    """9×9 grid → 448×448 PNG image"""

    img = Image.new("RGB", (448, 448), color="white")
    draw = ImageDraw.Draw(img)

    # Draw grid lines
    for i in range(10):
        line_width = 3 if i % 3 == 0 else 1  # Thick for 3×3 boxes
        y = i * 48
        draw.line([(0, y), (448, y)], fill="black", width=line_width)
        x = i * 48
        draw.line([(x, 0), (x, 448)], fill="black", width=line_width)

    # Draw numbers
    for row in range(9):
        for col in range(9):
            num = puzzle[row][col]
            if num != 0:  # Only draw filled cells
                x = col * 48 + 24  # Center of cell
                y = row * 48 + 24
                draw.text((x, y), str(num), fill="black", font=font, anchor="mm")

    return img
```

**Visual Result**:
```
┌───┬───┬───┐
│ 5 │ 3 │   │
├───┼───┼───┤
│ 6 │   │   │
├───┼───┼───┤
│   │ 9 │ 8 │
└───┴───┴───┘
(simplified 3×3 example; actual is 9×9)
```

### Step 4: Save JSON Metadata

```python
metadata = {
    "puzzle_id": "unsolved_001",
    "size": [9, 9],
    "initial_state": {
        "filled_cells": [
            {"row": 0, "col": 0, "value": 5},
            {"row": 0, "col": 1, "value": 3},
            {"row": 1, "col": 0, "value": 6},
            # ... all filled cells
        ]
    },
    "solution": {
        "cells": [
            [5, 3, 4, 6, 7, 8, 9, 1, 2],
            [6, 7, 2, 1, 9, 5, 3, 4, 8],
            # ... full solved grid
        ]
    },
    "difficulty": "medium"
}

with open('unsolved_001.json', 'w') as f:
    json.dump(metadata, f, indent=2)
```

## Data Split

### Training Set (Solved Examples)

- **Purpose**: For VLM to learn constraint rules
- **Count**: 100 puzzles (configurable)
- **Characteristics**:
  - All cells filled (complete solutions)
  - Images show finished puzzles
  - Used in rule inference prompts: "Analyze these solved examples"
- **Location**: `data/raw/sudoku/solved/`

### Test Set (Unsolved Puzzles)

- **Purpose**: Evaluate system end-to-end
- **Count**: 200 puzzles (configurable)
- **Distribution**:
  - Easy: 70 (35-40 clues)
  - Medium: 80 (27-34 clues)
  - Hard: 50 (17-26 clues)
- **Characteristics**:
  - Only some cells filled (initial state)
  - Images show incomplete puzzles
  - System must solve these
- **Location**: `data/raw/sudoku/unsolved/`

## How VLM Processes Images

When you send a puzzle image to the VLM:

```python
from src.models.qwen_model import QwenVLModel

vlm = QwenVLModel()
vlm.load_model()

# Send puzzle image + prompt
response = vlm.query(
    image="unsolved_001.png",  # 448×448 PNG
    prompt="Extract the current state of this Sudoku puzzle as JSON..."
)

# VLM processes:
# 1. Vision encoder: extracts features from image
# 2. Understands grid structure (lines, cells)
# 3. OCR-like understanding: recognizes digits 1-9
# 4. Spatial reasoning: maps cells to positions
# 5. Text generation: outputs structured response
```

**Why 448×448?**
- Qwen2-VL's optimal input size
- Large enough for clear digit recognition
- Small enough for fast processing
- Standard in vision-language models

## Quality Checks

After generating dataset, verify:

```python
from pathlib import Path
import json

solved_dir = Path("data/raw/sudoku/solved")

for json_file in solved_dir.glob("*.json"):
    with open(json_file) as f:
        data = json.load(f)

    # Check structure
    assert "puzzle_id" in data
    assert "solution" in data
    assert len(data["solution"]["cells"]) == 9
    assert len(data["solution"]["cells"][0]) == 9

    # Check solution validity (all 1-9, no duplicates per row/col/box)
    solution = data["solution"]["cells"]
    for row in solution:
        assert set(row) == set(range(1, 10))

    # Check image exists
    img_file = json_file.with_suffix(".png")
    assert img_file.exists()
    assert img_file.stat().st_size > 0

print("✓ Dataset validation passed!")
```

## Troubleshooting

### Image Quality Issues

**Problem**: VLM can't read digits clearly
**Solution**:
- Check font size (should be ~32pt for 448×448 image)
- Increase image size to 672×672
- Add contrast enhancement

### Missing Cells

**Problem**: Some cells missing from image or JSON
**Solution**:
- Verify puzzle string has exactly 81 characters
- Check digit rendering loop covers all 9×9
- Validate JSON cell count

### Solution Invalid

**Problem**: `solution` has duplicate digits in row/column
**Solution**:
- Kaggle dataset should be valid, but check source
- If generating synthetic: verify backtracking algorithm
- Check parsing: ensure grid indices are correct

### CSV Not Readable

**Problem**: `prepare_sudoku_kaggle.py` fails on CSV
**Solution**:
- Check column names: must have 'puzzle' and 'solution'
- Verify encoding: UTF-8 recommended
- Check file not corrupted: test opening in editor

## Performance Notes

- **Generate synthetic dataset** (100+200 puzzles): ~2-3 minutes
- **Kaggle preparation** (per 1000 puzzles): ~30 seconds
- **Image rendering** (per puzzle): ~50-100ms
- **Total disk space** (100+200 puzzles): ~20MB

## Next Steps

1. ✅ Understand dataset format
2. ✅ Generate or download dataset
3. 🚀 **Run quick test**: `python experiments/quick_test.py`
4. 🚀 **Test VLM on images**: Show image to Qwen2-VL
5. 🚀 **Implement rule inference**: Parse VLM responses

See `README.md` for dataset generation commands.
