# Phase 3: State Extraction Module - Complete

## What Was Implemented

### 1. **Prompt Templates** (`src/prompts/state_extraction_prompts.py`)

- `get_state_extraction_prompt()` - Main prompt for extracting puzzle state
  - Shows VLM a puzzle image
  - Asks VLM to identify all 81 cell values
  - Requests structured JSON output
  - Specifies exact coordinate system (0-indexed rows/cols)

- `get_state_validation_prompt()` - Validate extracted state
- `get_state_correction_prompt()` - Re-examine specific cells for corrections

**Key features:**
- Requests all cells (filled and empty) to be listed
- Asks for confidence scores
- Encourages flagging unclear cells
- Specifies 0-indexed coordinates (0-8, not 1-9)

### 2. **State Parser** (`src/parsers/state_parser.py`)

Extracts structured puzzle state from VLM natural language responses.

**Methods:**
- `parse_json_from_text()` - Extract JSON from VLM response
- `parse_state_from_json()` - Convert JSON to `PuzzleState`
- `parse_state_response()` - Complete pipeline
- `validate_state()` - Check for contradictions and errors

**Validation Checks:**
- Correct cell count (81 for 9×9)
- No duplicate values in any row
- No duplicate values in any column
- No duplicate values in any 3×3 box
- All values are 1-9

**Features:**
- Robust JSON extraction
- Cell-level error detection
- Comprehensive validation report
- Detailed error logging

### 3. **State Extraction Module** (`src/modules/state_extraction.py`)

Main orchestration class for puzzle state extraction.

**Core Method: `extract_state(puzzle_image, validate=True, auto_correct=False)`**
```python
extract_state(puzzle_image: Path) -> PuzzleState
```

**Pipeline:**
1. Load puzzle image
2. Create state extraction prompt
3. Query VLM to extract cell values
4. Parse VLM response into `PuzzleState`
5. Validate state (optional)
6. Auto-correct issues (optional)
7. Return `PuzzleState`

**Additional Features:**
- Auto-correction: When validation fails, re-query VLM for problematic cells
- Detailed logging at each step
- Context manager support for VLM lifecycle
- Flexible validation strategies

### 4. **Test Script** (`experiments/test_state_extraction.py`)

Test the complete state extraction pipeline.

**Usage:**
```bash
python experiments/test_state_extraction.py
```

**What it does:**
1. Loads 2 test puzzles
2. Initializes Qwen2-VL
3. Extracts state from each puzzle image
4. Validates extracted state
5. Displays sample grid for verification

## Data Flow

```
Puzzle Image (unsolved)
        ↓
State Extraction Prompt
        ↓
VLM Analysis
        ↓
Text Response (natural language + JSON)
        ↓
State Parser (extract JSON, parse cells)
        ↓
PuzzleState (filled cells + empty cells)
        ↓
Validation (check for contradictions)
        ↓
Output: Puzzle State Ready for CSP
```

## Expected Output

**VLM extracts:**
```json
{
  "grid_size": [9, 9],
  "filled_cells": [
    {"row": 0, "col": 0, "value": 5},
    {"row": 0, "col": 1, "value": 3},
    {"row": 0, "col": 2, "value": 4},
    ...
  ],
  "empty_cells": [
    {"row": 0, "col": 3},
    {"row": 0, "col": 4},
    ...
  ],
  "confidence": 0.95,
  "notes": "Image is clear with good contrast"
}
```

**Gets converted to:**
```python
PuzzleState(
  grid_size=(9, 9),
  filled_cells={
    (0, 0): 5,
    (0, 1): 3,
    (0, 2): 4,
    ...
  },
  empty_cells=[(0, 3), (0, 4), ...],
  domains={...}  # auto-generated
)
```

## Testing

### Quick Test
```bash
# Make sure you have test puzzles
python scripts/generate_synthetic_sudoku.py --quick

# Run state extraction test
python experiments/test_state_extraction.py
```

### Expected Output
```
STATE EXTRACTION TEST
============================================================

1. Loading test puzzles...
✓ Loaded 2 puzzles

2. Initializing VLM...
[Loading...]

3. Extracting puzzle states...

   Puzzle #1: unsolved_001
   Image: data/raw/sudoku/unsolved/unsolved_001.png
   ✓ Extracted state
     - Filled cells: 25
     - Empty cells: 56
   ✓ Validation passed

   Extracted Grid (first 3 rows):
     Row 0: 5 3 . 6 7 8 9 1 2
     Row 1: 6 . . 1 9 5 3 4 8
     Row 2: . 9 8 3 4 2 5 6 1
```

## Key Design Decisions

1. **Cell Representation**: 0-indexed (0-8) instead of 1-indexed
   - Pro: Standard in programming
   - Con: Requires careful coordinate mapping

2. **Complete Cell Listing**: Requires both filled_cells and empty_cells
   - Pro: Explicit, easier to validate
   - Con: More verbose

3. **Validation Strategy**: Multi-level checks
   - Cell count, row/col/box uniqueness, value ranges
   - Comprehensive error reporting
   - Optional auto-correction

4. **Auto-Correction**: Re-queries VLM for problematic cells
   - Pro: Can fix perception errors
   - Con: Additional VLM queries cost time/tokens

## Integration with Other Phases

### Inputs from Previous Phases
- **Phase 1**:
  - VLM interface (`QwenVLModel`)
  - Puzzle image loading
  - Config system

- **Phase 2**:
  - Pattern of VLM querying
  - JSON parsing approach

### Outputs for Next Phases
- **Phase 4** (CSP Translation):
  - Takes `PuzzleState` from this phase
  - Uses with inferred `ConstraintRuleSet` from Phase 2
  - Builds CSP for solving

- **Phase 5** (Evaluation):
  - Evaluates accuracy of state extraction
  - Measures cell-level accuracy vs ground truth

## Potential Issues & Solutions

**Problem:** VLM confuses digit 0 and O (letter O)
- **Solution:** Prompt emphasizes "digits 1-9 only" or implement OCR fallback

**Problem:** Cell boundaries unclear in image
- **Solution:** Auto-correction queries unclear cells, flag in confidence

**Problem:** VLM uses 1-indexed instead of 0-indexed
- **Solution:** Validate coordinates, auto-correct if off-by-one pattern detected

**Problem:** Incomplete cell list (not all 81 accounted for)
- **Solution:** Validation check catches this, triggers re-examination

## TODOs for Enhancement

- [ ] OCR fallback for ambiguous digit recognition
- [ ] Per-cell confidence scores (not just overall)
- [ ] Better auto-correction heuristics
- [ ] Support for rotated/skewed images
- [ ] Handling for partially visible grids
- [ ] Image preprocessing (contrast, brightness)
- [ ] Confidence-based cell re-examination (query only low-confidence cells)
- [ ] Multiple extraction attempts with different prompts

## Related Files

- **Config**: `src/config.py`
- **VLM**: `src/models/qwen_model.py`
- **Data**: `src/core/puzzle_state.py`, `src/data/dataset.py`
- **Prompts**: `src/prompts/state_extraction_prompts.py`
- **Parser**: `src/parsers/state_parser.py`
- **Module**: `src/modules/state_extraction.py`
- **Test**: `experiments/test_state_extraction.py`

## Next Phase

**Phase 4: CSP Translation & Solving**
- Combine inferred rules (Phase 2) + extracted state (Phase 3)
- Build formal CSP problem
- Solve using CSP solver
- This is where all pieces come together!
