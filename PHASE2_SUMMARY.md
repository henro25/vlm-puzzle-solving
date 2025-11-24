# Phase 2: Rule Inference Module - Complete

## What Was Implemented

### 1. **Prompt Templates** (`src/prompts/rule_inference_prompts.py`)

- `get_rule_inference_prompt()` - Main prompt for analyzing solved examples
  - Shows VLM N solved Sudoku puzzles
  - Asks VLM to identify common constraint rules
  - Requests structured JSON output
  - Specifies exact output format for parsing

- `get_rule_validation_prompt()` - Validate inferred rules
- `get_few_shot_example()` - Example of expected output format

**Key features:**
- Requests JSON output for easy parsing
- Specifies rule types: `all_different`, `sum`, `arithmetic`, `adjacency`, `custom`
- Asks for reasoning and confidence scores
- Designed for multi-image input (analyzes multiple solved examples)

### 2. **Rule Parser** (`src/parsers/rule_parser.py`)

Extracts structured rules from VLM natural language responses.

**Methods:**
- `parse_json_from_text()` - Extract JSON from VLM response (handles embedded JSON)
- `parse_rules_from_json()` - Convert JSON to `ConstraintRuleSet`
- `_generate_scope_from_type()` - Create variable scope lists (e.g., `["row_0", ..., "row_8"]`)
- `parse_rule_response()` - Complete pipeline

**Features:**
- Robust JSON extraction (handles text before/after JSON)
- Type validation for constraint types
- Scope generation for Sudoku variables
- Error logging at each step
- Returns structured `ConstraintRuleSet` objects

### 3. **Rule Inference Module** (`src/modules/rule_inference.py`)

Main orchestration class for the rule learning pipeline.

**Core Method: `infer_rules(examples, validate=True)`**
```python
infer_rules(examples: List[SudokuPuzzle]) -> ConstraintRuleSet
```

**Pipeline:**
1. Load puzzle images from examples
2. Create rule inference prompt
3. Query VLM with puzzle images
4. Parse VLM response into structured rules
5. Validate rules against examples
6. Return `ConstraintRuleSet`

**Additional Methods:**
- `validate_rules()` - Check rules don't contradict examples
- `refine_rules_with_feedback()` - Improve rules based on feedback
- Context manager support (auto load/unload VLM)

### 4. **Test Script** (`experiments/test_rule_inference.py`)

Test the complete rule inference pipeline.

**Usage:**
```bash
python experiments/test_rule_inference.py
```

**What it does:**
1. Loads 3 training examples
2. Initializes Qwen2-VL
3. Runs rule inference
4. Displays inferred rules and confidence

## Data Flow

```
SudokuPuzzle Images (solved examples)
        ↓
Prepare Prompt + Images
        ↓
VLM Analysis
        ↓
Text Response (natural language + JSON)
        ↓
Rule Parser (extract JSON, parse rules)
        ↓
ConstraintRuleSet (formal representation)
        ↓
Validation (check against examples)
        ↓
Output: Inferred Rules Ready for CSP Solving
```

## Expected Output

**VLM infers:**
```json
{
  "rules": [
    {
      "type": "all_different",
      "scope": "row",
      "description": "Each row must contain all digits 1-9 exactly once",
      "applies_to": ["row_0", "row_1", ..., "row_8"]
    },
    {
      "type": "all_different",
      "scope": "column",
      "description": "Each column must contain all digits 1-9 exactly once",
      "applies_to": ["col_0", "col_1", ..., "col_8"]
    },
    {
      "type": "all_different",
      "scope": "box",
      "description": "Each 3×3 box must contain all digits 1-9 exactly once",
      "applies_to": ["box_0", "box_1", ..., "box_8"]
    }
  ],
  "confidence": 0.99,
  "reasoning": "All three rules..."
}
```

**Gets converted to:**
```python
ConstraintRuleSet(
  rules=[
    ConstraintRule(type=ConstraintType.ALL_DIFFERENT, scope=["row_0", ...]),
    ConstraintRule(type=ConstraintType.ALL_DIFFERENT, scope=["col_0", ...]),
    ConstraintRule(type=ConstraintType.ALL_DIFFERENT, scope=["box_0", ...])
  ],
  metadata={"confidence": 0.99, "reasoning": "..."}
)
```

## Testing

### Quick Test
```bash
# Make sure you have training examples
python scripts/generate_synthetic_sudoku.py --quick

# Run rule inference test
python experiments/test_rule_inference.py
```

### Expected Issues & Solutions

**Problem:** VLM returns text without JSON
- **Solution:** Parser looks for JSON blocks in text, will log error and return None

**Problem:** Unknown constraint types
- **Solution:** Parser converts to `ConstraintType.CUSTOM`, logs warning

**Problem:** Missing scope information
- **Solution:** Parser generates scope from scope_type (e.g., "row" → ["row_0", ..., "row_8"])

## Integration with Other Phases

### Inputs from Previous Phases
- **Phase 1**:
  - VLM interface (`QwenVLModel`)
  - Dataset loading (`SudokuDataset`)
  - Config system
  - Core data structures

### Outputs for Next Phases
- **Phase 3** (State Extraction):
  - Learned `ConstraintRuleSet` (rules from this phase)
  - Pattern of VLM querying (similar structure)

- **Phase 4** (CSP Translation):
  - Takes inferred rules from this phase
  - Converts to CSP constraints

- **Phase 5** (Evaluation):
  - Evaluates quality of inferred rules
  - Measures rule precision/recall

## Key Design Decisions

1. **VLM Instruction Format**: JSON output
   - Pro: Easy to parse, structured
   - Con: Some VLMs may struggle with complex JSON

2. **Constraint Types**: Predefined set (all_different, sum, arithmetic, etc.)
   - Pro: Standardized for CSP solver
   - Con: May miss novel constraint types

3. **Validation Strategy**: Currently basic
   - Checks rules don't contradict examples
   - TODO: More sophisticated validation

4. **Multi-Image Handling**: Uses first image with context
   - Current: Sends one image to VLM
   - TODO: Proper batch image support for multi-example analysis

## TODOs for Enhancement

- [ ] Support batch image queries (multiple examples at once)
- [ ] More sophisticated rule validation
- [ ] Handle conflicting rule suggestions
- [ ] Confidence scoring per rule
- [ ] Rule filtering (remove redundant rules)
- [ ] Support for more constraint types
- [ ] Interactive refinement loop
- [ ] Rule generalization testing

## Related Files

- **Config**: `src/config.py`
- **VLM**: `src/models/qwen_model.py`, `src/models/vlm_interface.py`
- **Data**: `src/data/dataset.py`, `src/data/loaders.py`
- **Rules**: `src/core/constraint_rules.py`
- **Utils**: `src/parsers/rule_parser.py`, `src/prompts/rule_inference_prompts.py`

## Next Phase

**Phase 3: State Extraction Module**
- VLM extracts puzzle state from unsolved puzzle images
- Identifies filled cells and their values
- Determines empty cell domains
- Similar pipeline to rule inference but for puzzle perception
