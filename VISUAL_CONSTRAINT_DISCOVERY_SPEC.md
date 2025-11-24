# Visual Constraint Discovery: Project Specification

**Project Type**: Compositional AI Research Project  
**Duration**: 3-4 weeks  
**Hardware**: A100/H100 GPUs available  
**Goal**: Build a neurosymbolic system where Vision-Language Models learn constraint structures from visual examples, then use CSP solvers to solve new puzzles.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Implementation Phases](#implementation-phases)
4. [Technical Stack](#technical-stack)
5. [Detailed Module Specifications](#detailed-module-specifications)
6. [Evaluation Framework](#evaluation-framework)
7. [Dataset Specifications](#dataset-specifications)
8. [Research Extensions](#research-extensions)

---

## Project Overview

### Core Research Question
**Can Vision-Language Models inductively learn constraint structures from visual examples and apply them to solve new constraint satisfaction problems?**

### What Makes This Novel
- No hardcoded constraint rules (unlike basic VLM + Sudoku solver)
- VLM must perform inductive reasoning (examples → rules)
- Tests compositional understanding in multimodal systems
- Bridges neural perception with symbolic reasoning
- Applicable to arbitrary constraint puzzles

### System Flow
```
Input: [Solved Example 1, Solved Example 2, ..., Solved Example N, New Unsolved Puzzle]
                                    ↓
Step 1: VLM analyzes solved examples → Infers constraint rules
                                    ↓
Step 2: VLM extracts state from new puzzle → Initial configuration
                                    ↓
Step 3: Build CSP from inferred rules + initial state
                                    ↓
Step 4: CSP Solver finds solution
                                    ↓
Output: Solution + Evaluation of inferred rules
```

---

## System Architecture

### High-Level Components

```
┌─────────────────────────────────────────────────────────────┐
│                    VISUAL CONSTRAINT DISCOVERY               │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────┐
│  Solved Examples     │
│  (Training Images)   │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────────────────┐
│  COMPONENT 1:                    │
│  Rule Inference Module           │
│                                  │
│  • VLM analyzes examples         │
│  • Extracts constraint patterns  │
│  • Generates formal rules        │
│  • Output: ConstraintRuleSet     │
└──────────┬───────────────────────┘
           │
           │  ┌─────────────────┐
           │  │  New Unsolved   │
           │  │  Puzzle Image   │
           │  └────────┬────────┘
           │           │
           ▼           ▼
┌──────────────────────────────────┐
│  COMPONENT 2:                    │
│  State Extraction Module         │
│                                  │
│  • VLM extracts puzzle state     │
│  • Identifies variables/domains  │
│  • Output: PuzzleState           │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│  COMPONENT 3:                    │
│  CSP Translation Module          │
│                                  │
│  • Combines rules + state        │
│  • Builds formal CSP             │
│  • Output: CSPProblem            │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│  COMPONENT 4:                    │
│  CSP Solver                      │
│                                  │
│  • Solves constraint problem     │
│  • Finds valid assignment        │
│  • Output: Solution              │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│  COMPONENT 5:                    │
│  Evaluation & Verification       │
│                                  │
│  • Validates solution            │
│  • Measures accuracy             │
│  • Analyzes failure modes        │
└──────────────────────────────────┘
```

### Data Flow

```
Input: solved_examples, new_puzzle
  ↓
rules = RuleInferenceModule.infer(solved_examples)
  ↓
state = StateExtractionModule.extract(new_puzzle)
  ↓
csp = CSPTranslator.build(rules, state)
  ↓
solution = CSPSolver.solve(csp)
  ↓
metrics = Evaluator.evaluate(solution, ground_truth)
  ↓
Output: solution, metrics
```

---

## Implementation Phases

### Phase 1: Foundation & Infrastructure (Week 1)
**Goal**: Set up project structure, data pipeline, and basic VLM integration

**Key Tasks**:
1. Create modular project structure with clear separation of concerns
2. Implement dataset loading for puzzle images (Sudoku initially)
3. Set up VLM API integration (start with API-based like Claude/GPT-4V)
4. Create configuration system for model selection and hyperparameters
5. Set up logging and experiment tracking
6. Write basic image preprocessing utilities

**Deliverables**:
- Working project structure
- Can load puzzle datasets
- Can query VLM with images
- Configuration system in place

**Files to Create**:
- `src/config.py` - Configuration
- `src/data/dataset.py` - Dataset classes
- `src/data/loaders.py` - Data loading
- `src/models/vlm_interface.py` - VLM abstraction
- `src/utils/logging.py` - Logging utilities
- `src/utils/image_processing.py` - Image preprocessing

**Success Criteria**:
- Can load 100+ Sudoku images
- Can send image + prompt to VLM and get response
- All paths/configs managed centrally

---

### Phase 2: Rule Inference Module (Week 1-2)
**Goal**: Implement the core novelty - VLM learns constraint rules from examples

**Key Tasks**:
1. Design prompt templates for rule inference
2. Implement few-shot learning approach (show VLM solved examples)
3. Parse VLM output into structured constraint representation
4. Create ConstraintRule data structures
5. Implement validation of inferred rules
6. Add support for different constraint types (AllDifferent, Sum, etc.)

**Core Challenge**: Convert natural language rule descriptions → formal constraints

**Deliverables**:
- `RuleInferenceModule` class that takes solved examples and outputs formal rules
- Support for at least 3 constraint types initially
- Validation logic for checking rule consistency

**Files to Create**:
- `src/modules/rule_inference.py` - Main module
- `src/core/constraint_rules.py` - Rule data structures
- `src/prompts/rule_inference_prompts.py` - Prompt templates
- `src/parsers/rule_parser.py` - Parse VLM output to rules

**Success Criteria**:
- Given 5 solved Sudoku images, can extract rules like "each row must have different values 1-9"
- Rules are in machine-readable format
- Works on at least one puzzle type (Sudoku)

---

### Phase 3: State Extraction Module (Week 2)
**Goal**: VLM extracts puzzle state from images (what's filled, what's empty)

**Key Tasks**:
1. Design prompts for state extraction
2. Implement structured output parsing (JSON format)
3. Create PuzzleState data structure
4. Add validation for extracted states
5. Handle edge cases (unclear images, partial occlusion)
6. Implement confidence scoring if possible

**Core Challenge**: Accurate perception of visual puzzle state

**Deliverables**:
- `StateExtractionModule` that converts puzzle image → structured state
- High accuracy (>90%) on clear images
- Graceful degradation on noisy images

**Files to Create**:
- `src/modules/state_extraction.py` - Main module
- `src/core/puzzle_state.py` - State data structures
- `src/prompts/state_extraction_prompts.py` - Prompt templates
- `src/parsers/state_parser.py` - Parse VLM output to state

**Success Criteria**:
- Can extract Sudoku state with >90% cell accuracy
- Outputs structured representation (which cells filled, domains for empty cells)
- Handles 9x9 Sudoku reliably

---

### Phase 4: CSP Translation & Solving (Week 2)
**Goal**: Convert inferred rules + extracted state into solvable CSP

**Key Tasks**:
1. Choose CSP solver library (python-constraint or python-minizinc)
2. Implement translation from ConstraintRules → CSP constraints
3. Implement translation from PuzzleState → CSP variables/domains
4. Connect everything into formal CSP problem
5. Solve CSP and extract solution
6. Add timeout/failure handling

**Core Challenge**: Bridging symbolic representations to CSP solver format

**Deliverables**:
- `CSPTranslator` that builds CSP from rules + state
- `CSPSolver` wrapper that solves and returns solution
- End-to-end pipeline working

**Files to Create**:
- `src/modules/csp_translator.py` - Translation logic
- `src/solvers/csp_solver.py` - Solver wrapper
- `src/core/csp_problem.py` - CSP representation

**Success Criteria**:
- Can convert rules + state into valid CSP
- CSP solver finds correct solution for valid puzzles
- Detects when puzzle is unsolvable

---

### Phase 5: Evaluation & Experimentation (Week 3)
**Goal**: Comprehensive evaluation of the system

**Key Tasks**:
1. Create evaluation metrics (accuracy, precision, recall, etc.)
2. Implement error analysis tools
3. Build comparison baselines (pure VLM end-to-end)
4. Run systematic experiments across difficulty levels
5. Analyze failure modes
6. Create visualizations of results

**Evaluation Dimensions**:
- **Rule Inference Accuracy**: Are inferred rules correct?
- **State Extraction Accuracy**: Cell-level accuracy
- **End-to-End Success Rate**: % of puzzles solved correctly
- **Comparison**: VLM+CSP vs Pure VLM
- **Ablation**: Impact of number of examples, prompt variations

**Files to Create**:
- `src/evaluation/metrics.py` - Metric computation
- `src/evaluation/evaluator.py` - Evaluation orchestration
- `src/evaluation/error_analysis.py` - Failure mode analysis
- `src/experiments/run_experiments.py` - Experiment runner
- `src/visualization/plot_results.py` - Result visualization

**Success Criteria**:
- Complete evaluation on 100+ test puzzles
- Clear understanding of where system fails
- Quantitative comparison with baseline
- Publication-ready figures

---

### Phase 6: Extensions & Polish (Week 3-4)
**Goal**: Implement at least one research extension

**Extension Options** (choose 1-2):

**Option A: Multiple Puzzle Types**
- Extend to Kakuro, KenKen, or other constraint puzzles
- Test rule inference generalization
- Measure zero-shot transfer

**Option B: Uncertainty Handling**
- VLM outputs confidence scores
- Try multiple rule interpretations
- Implement robust solving

**Option C: Interactive Verification**
- When CSP fails, ask VLM to double-check
- Implement human-in-the-loop verification
- Active learning approach

**Option D: Hierarchical Constraint Discovery**
- Decompose complex puzzles into subproblems
- Learn rules at multiple abstraction levels
- Compositional reasoning (fits course theme!)

**Files to Create** (depends on extension):
- Extension-specific modules in `src/extensions/`
- Additional evaluation scripts
- Extended experiment configurations

---

## Technical Stack

### Required Libraries

**Core Dependencies**:
```
# VLM Access
anthropic>=0.18.0        # For Claude API
openai>=1.0.0            # For GPT-4V API (optional)
pillow>=10.0.0           # Image processing
requests>=2.31.0         # HTTP requests

# CSP Solving
python-constraint>=1.4.0  # Primary CSP solver (simple, good for learning)
# OR
minizinc>=0.9.0          # Alternative (more powerful, research-grade)

# Data & ML
numpy>=1.24.0
pandas>=2.0.0            # For data analysis
torch>=2.0.0             # If using local VLMs
transformers>=4.30.0     # For LLaVA or other local VLMs

# Visualization & Analysis
matplotlib>=3.7.0
seaborn>=0.12.0
plotly>=5.14.0           # Interactive plots

# Utilities
python-dotenv>=1.0.0     # Environment management
pydantic>=2.0.0          # Data validation
tqdm>=4.65.0             # Progress bars
loguru>=0.7.0            # Better logging
```

**Development Dependencies**:
```
pytest>=7.3.0            # Testing
black>=23.0.0            # Code formatting
ruff>=0.0.270            # Linting
```

### Project Structure

```
visual-constraint-discovery/
├── README.md
├── requirements.txt
├── setup.py
├── .env.example
├── .gitignore
│
├── data/
│   ├── raw/                    # Original puzzle images
│   │   ├── sudoku/
│   │   │   ├── solved/         # Solved examples for rule learning
│   │   │   └── unsolved/       # Test puzzles
│   │   ├── kakuro/             # (Extension)
│   │   └── kenken/             # (Extension)
│   ├── processed/              # Processed/cached data
│   └── ground_truth/           # Ground truth labels
│
├── src/
│   ├── __init__.py
│   │
│   ├── config.py               # Configuration management
│   │
│   ├── core/                   # Core data structures
│   │   ├── __init__.py
│   │   ├── constraint_rules.py # ConstraintRule classes
│   │   ├── puzzle_state.py     # PuzzleState classes
│   │   └── csp_problem.py      # CSP representation
│   │
│   ├── data/                   # Data loading
│   │   ├── __init__.py
│   │   ├── dataset.py          # Dataset classes
│   │   └── loaders.py          # Data loaders
│   │
│   ├── models/                 # VLM interfaces
│   │   ├── __init__.py
│   │   ├── vlm_interface.py    # Abstract base class
│   │   ├── claude_model.py     # Claude implementation
│   │   ├── gpt4v_model.py      # GPT-4V implementation
│   │   └── llava_model.py      # Local LLaVA (optional)
│   │
│   ├── modules/                # Core system modules
│   │   ├── __init__.py
│   │   ├── rule_inference.py   # COMPONENT 1
│   │   ├── state_extraction.py # COMPONENT 2
│   │   └── csp_translator.py   # COMPONENT 3
│   │
│   ├── solvers/                # CSP solvers
│   │   ├── __init__.py
│   │   ├── csp_solver.py       # COMPONENT 4
│   │   └── solver_utils.py
│   │
│   ├── prompts/                # Prompt templates
│   │   ├── __init__.py
│   │   ├── rule_inference_prompts.py
│   │   ├── state_extraction_prompts.py
│   │   └── prompt_utils.py
│   │
│   ├── parsers/                # Output parsers
│   │   ├── __init__.py
│   │   ├── rule_parser.py
│   │   └── state_parser.py
│   │
│   ├── evaluation/             # COMPONENT 5
│   │   ├── __init__.py
│   │   ├── metrics.py
│   │   ├── evaluator.py
│   │   └── error_analysis.py
│   │
│   ├── visualization/          # Plotting & visualization
│   │   ├── __init__.py
│   │   ├── plot_results.py
│   │   └── puzzle_viz.py
│   │
│   ├── utils/                  # Utilities
│   │   ├── __init__.py
│   │   ├── logging.py
│   │   └── image_processing.py
│   │
│   └── extensions/             # Research extensions
│       ├── __init__.py
│       ├── uncertainty.py
│       ├── interactive.py
│       └── hierarchical.py
│
├── experiments/                # Experiment scripts
│   ├── run_baseline.py
│   ├── run_main_experiment.py
│   ├── run_ablation.py
│   └── configs/                # Experiment configs
│
├── notebooks/                  # Jupyter notebooks for exploration
│   ├── 01_data_exploration.ipynb
│   ├── 02_rule_inference_test.ipynb
│   ├── 03_state_extraction_test.ipynb
│   └── 04_results_analysis.ipynb
│
├── tests/                      # Unit tests
│   ├── test_rule_inference.py
│   ├── test_state_extraction.py
│   ├── test_csp_solver.py
│   └── test_integration.py
│
└── results/                    # Experiment outputs
    ├── figures/
    ├── metrics/
    └── logs/
```

---

## Detailed Module Specifications

### Component 1: Rule Inference Module

**Purpose**: Analyze solved puzzle examples and infer constraint rules

**Input**: 
- List of solved puzzle images (typically 3-10 examples)
- Puzzle type (optional hint)

**Output**:
- `ConstraintRuleSet` object containing:
  - List of constraint rules
  - Variable definitions
  - Domain specifications

**Key Methods**:
```
RuleInferenceModule:
  - infer_rules(solved_examples) → ConstraintRuleSet
  - validate_rules(rules) → bool
  - refine_rules_with_feedback(rules, feedback) → ConstraintRuleSet
```

**Prompt Strategy**:
1. Show VLM 3-5 solved puzzle images
2. Ask: "What are the rules that all solutions follow?"
3. Request structured output (JSON format)
4. Parse and validate

**Constraint Types to Support**:
- `AllDifferent`: Variables must have different values
- `Sum`: Variables must sum to target
- `Arithmetic`: General arithmetic constraints
- `Adjacency`: Spatial/neighbor constraints

**Data Structures**:
```
ConstraintRule:
  - type: str (e.g., "all_different", "sum", "arithmetic")
  - scope: List[str] (variable names affected)
  - parameters: Dict (constraint-specific params)

ConstraintRuleSet:
  - rules: List[ConstraintRule]
  - variables: Dict[str, VariableSpec]
  - domains: Dict[str, List[Any]]
```

---

### Component 2: State Extraction Module

**Purpose**: Extract current puzzle state from image

**Input**:
- Single puzzle image (unsolved or partially solved)
- Puzzle type (for contextualization)

**Output**:
- `PuzzleState` object containing:
  - Grid/structure information
  - Filled cells with values
  - Empty cells with candidate domains

**Key Methods**:
```
StateExtractionModule:
  - extract_state(puzzle_image) → PuzzleState
  - validate_state(state) → bool
  - get_confidence_scores(state) → Dict[cell, float]
```

**Prompt Strategy**:
1. Show VLM the puzzle image
2. Ask for structured extraction of all cells
3. Request JSON format with cell coordinates and values
4. Parse and validate against physical constraints

**Error Handling**:
- Retry extraction if validation fails
- Request VLM to re-examine specific cells
- Flag low-confidence extractions

**Data Structures**:
```
PuzzleState:
  - grid_size: Tuple[int, int]
  - filled_cells: Dict[position, value]
  - empty_cells: List[position]
  - domains: Dict[position, List[value]]
  - confidence: Dict[position, float] (optional)
```

---

### Component 3: CSP Translator

**Purpose**: Convert rules + state into formal CSP

**Input**:
- `ConstraintRuleSet` from rule inference
- `PuzzleState` from state extraction

**Output**:
- `CSPProblem` object ready for solving

**Key Methods**:
```
CSPTranslator:
  - translate(rules, state) → CSPProblem
  - add_constraint(csp, rule) → None
  - add_variables(csp, state) → None
```

**Translation Logic**:
1. Create CSP variables from puzzle cells
2. Set domains based on filled/empty cells
3. Add constraints from inferred rules
4. Validate CSP is well-formed

**Data Structures**:
```
CSPProblem:
  - variables: Dict[str, Variable]
  - domains: Dict[str, List[value]]
  - constraints: List[Constraint]
  - metadata: Dict (for tracking)
```

---

### Component 4: CSP Solver

**Purpose**: Solve the constraint satisfaction problem

**Input**:
- `CSPProblem` from translator

**Output**:
- Solution (variable assignment) or None if unsolvable

**Key Methods**:
```
CSPSolver:
  - solve(csp_problem) → Optional[Solution]
  - solve_with_timeout(csp_problem, timeout) → Optional[Solution]
  - get_all_solutions(csp_problem) → List[Solution]
```

**Solver Configuration**:
- Algorithm: Backtracking with constraint propagation
- Heuristics: Minimum Remaining Values (MRV)
- Timeout: 60 seconds default
- Early termination on first solution

---

### Component 5: Evaluation & Verification

**Purpose**: Measure system performance and analyze errors

**Input**:
- Predicted solutions
- Ground truth solutions
- System intermediate outputs

**Output**:
- Comprehensive metrics
- Error analysis reports
- Visualization plots

**Key Metrics**:

1. **Rule Inference Metrics**:
   - Rule precision: % of inferred rules that are correct
   - Rule recall: % of true rules that were inferred
   - Rule F1 score

2. **State Extraction Metrics**:
   - Cell accuracy: % of cells correctly extracted
   - Precision/Recall per cell type
   - Confidence calibration (if available)

3. **End-to-End Metrics**:
   - Solving success rate: % of puzzles solved correctly
   - Solution correctness: % of solutions that are valid
   - Time to solution

4. **Comparative Metrics**:
   - VLM+CSP vs Pure VLM end-to-end
   - Ablation: effect of number of examples
   - Ablation: effect of prompt variations

**Key Methods**:
```
Evaluator:
  - evaluate_rule_inference(inferred, ground_truth) → Dict[metric, value]
  - evaluate_state_extraction(extracted, ground_truth) → Dict[metric, value]
  - evaluate_end_to_end(solutions, ground_truth) → Dict[metric, value]
  - analyze_failures(failed_cases) → ErrorAnalysisReport
  - compare_baselines(results_a, results_b) → ComparisonReport
```

---

## Dataset Specifications

### Sudoku Dataset (Primary)

**Training Set** (for rule inference):
- 100 solved 9x9 Sudoku puzzles
- Clear, high-quality images
- Variety of difficulty levels
- Include grid lines visible

**Test Set** (for evaluation):
- 200 unsolved 9x9 Sudoku puzzles with known solutions
- Split by difficulty:
  - 70 easy (35-40 clues)
  - 80 medium (27-34 clues)
  - 50 hard (17-26 clues)

**Data Format**:
```
data/raw/sudoku/
├── solved/
│   ├── solved_001.png
│   ├── solved_001_solution.json  # Ground truth
│   └── ...
└── unsolved/
    ├── unsolved_001.png
    ├── unsolved_001_initial.json   # Initial state
    ├── unsolved_001_solution.json  # Ground truth solution
    └── ...
```

**Ground Truth Format** (JSON):
```
{
  "puzzle_id": "sudoku_001",
  "size": [9, 9],
  "initial_state": {
    "filled_cells": [
      {"row": 1, "col": 1, "value": 5},
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
  "rules": {
    "row_constraints": "all_different",
    "col_constraints": "all_different",
    "box_constraints": "all_different"
  },
  "difficulty": "medium"
}
```

### Data Generation Options

**Option A: Use Existing Datasets**
- Download from Kaggle: "1 million Sudoku puzzles"
- Render as images using PIL/matplotlib

**Option B: Generate Synthetic**
- Use Sudoku generation library
- Render with varying styles (grid thickness, fonts)
- Add controlled noise for robustness testing

**Option C: Real Images**
- Photograph physical Sudoku puzzles
- Include variety of lighting/angles
- More realistic but requires labeling

**Recommendation**: Start with Option A (fastest), add Option B for variety

---

## Evaluation Framework

### Experimental Protocol

**Baseline Comparisons**:

1. **Pure VLM End-to-End**
   - Prompt: "Solve this Sudoku puzzle"
   - No CSP solver, just VLM reasoning
   - Measures: accuracy, time

2. **VLM + Hardcoded CSP** (ablation)
   - Use handcrafted Sudoku rules (not learned)
   - VLM only does state extraction
   - Tests if rule learning is beneficial

3. **VLM + Learned CSP** (proposed system)
   - Learn rules from examples
   - Full pipeline

**Ablation Studies**:

1. **Number of Training Examples**
   - Vary: 1, 3, 5, 10, 20 solved examples
   - Measure: rule inference quality vs. number

2. **Prompt Variations**
   - Test different prompt templates
   - Few-shot vs. zero-shot
   - Chain-of-thought prompting

3. **VLM Model Comparison**
   - Claude Sonnet 4
   - GPT-4V
   - LLaVA (if time permits)

**Error Analysis**:

Categorize failures into:
- **Perception Errors**: State extraction wrong
- **Rule Inference Errors**: Inferred rules incorrect
- **CSP Errors**: Valid CSP but wrong solution
- **Unsolvable**: Puzzle has no solution (rare)

For each error type:
- Count frequency
- Identify patterns
- Propose mitigation strategies

### Metrics Dashboard

Create automated dashboard showing:
- Overall success rate (large number at top)
- Breakdown by difficulty level (bar chart)
- Error type distribution (pie chart)
- Comparison with baselines (side-by-side bars)
- Example successes and failures (image grid)
- Runtime statistics (box plot)

---

## Research Extensions

### Extension A: Hierarchical Constraint Discovery

**Motivation**: Complex puzzles have constraints at multiple levels

**Approach**:
1. VLM identifies high-level structure (e.g., 3x3 boxes in Sudoku)
2. VLM infers constraints at each level:
   - Cell-level: individual values
   - Row/col-level: all-different constraints
   - Box-level: all-different within boxes
   - Global-level: entire grid properties
3. Build hierarchical CSP with sub-problems
4. Solve compositionally

**Why Novel**: Mirrors human problem-solving, tests compositional reasoning

**Implementation Plan**:
- Add `HierarchicalRuleInference` module
- Modify CSP translator for hierarchical problems
- Solve sub-problems independently, then combine

**Evaluation**:
- Compare flat vs. hierarchical solving time
- Test on larger puzzles (16x16 Sudoku)
- Measure if hierarchy improves rule learning

---

### Extension B: Uncertainty-Aware Solving

**Motivation**: VLM perception is noisy

**Approach**:
1. VLM outputs confidence scores for each extracted cell
2. For low-confidence cells, try multiple values
3. Build multiple candidate CSPs
4. Select solution that appears in most CSPs (consensus)
5. Alternatively: use probabilistic CSP

**Why Novel**: Addresses perception-reasoning gap explicitly

**Implementation Plan**:
- Modify state extraction to return confidences
- Implement CSP enumeration for uncertain cells
- Add consensus voting mechanism

**Evaluation**:
- Test on noisy/degraded images
- Measure robustness improvement
- Analyze when uncertainty helps most

---

### Extension C: Interactive Verification Loop

**Motivation**: Human-in-the-loop when system is uncertain

**Approach**:
1. System attempts to solve
2. If CSP is unsatisfiable → something wrong
3. Identify most suspicious cells (via heuristics)
4. Ask VLM to re-examine those specific cells
5. Update state and retry
6. Optionally: ask human to verify specific cells

**Why Novel**: Active learning approach, addresses failure modes

**Implementation Plan**:
- Add `InteractiveVerifier` module
- Implement suspicion scoring (which cells likely wrong?)
- Add VLM re-prompting logic
- (Optional) Add human verification interface

**Evaluation**:
- Measure improvement in success rate with feedback
- Count number of interactions needed
- Compare to no-feedback baseline

---

### Extension D: Multi-Puzzle Generalization

**Motivation**: Can learned approach transfer across puzzle types?

**Approach**:
1. Start with Sudoku
2. Extend to Kakuro (sum constraints)
3. Extend to KenKen (arithmetic constraints)
4. Test zero-shot transfer: train on Sudoku, test on Kakuro

**Why Novel**: Tests generalization of learned approach

**Implementation Plan**:
- Add datasets for Kakuro and KenKen
- Minimal code changes (should work automatically!)
- Test cross-puzzle transfer

**Evaluation**:
- Within-puzzle accuracy
- Cross-puzzle transfer accuracy
- Analyze which constraint types transfer

---

## Implementation Strategy for Claude Code

### How to Use This Specification

**Step-by-Step Approach**:

1. **Read this entire document first** to understand system architecture

2. **Start with Phase 1** (Foundation):
   - Create project structure exactly as specified
   - Implement one module at a time
   - Test each module before moving on
   - Ask clarifying questions if anything is unclear

3. **For each component**:
   - Read the component specification carefully
   - Understand inputs, outputs, and key methods
   - Implement following the data structures provided
   - Write unit tests as you go
   - Test with simple examples before full integration

4. **Integration**:
   - Connect components in order: 1 → 2 → 3 → 4 → 5
   - Test end-to-end pipeline with 1-2 examples
   - Debug any integration issues
   - Scale up to full evaluation

5. **Experiments & Extensions**:
   - Run baseline experiments first
   - Implement one extension if time permits
   - Focus on reproducibility and documentation

### Key Principles

- **Modularity**: Each component should be independent and testable
- **Abstraction**: Use abstract base classes for flexibility (e.g., VLM interface)
- **Validation**: Validate at every step (rule validation, state validation, CSP validation)
- **Logging**: Log everything for debugging and analysis
- **Configuration**: All hyperparameters in config files, not hardcoded
- **Documentation**: Docstrings for all classes and methods

### Testing Strategy

**Unit Tests** (write as you implement):
- Test each module independently
- Mock VLM responses for deterministic testing
- Test edge cases and error handling

**Integration Tests**:
- Test full pipeline with known examples
- Test with ground truth data
- Verify end-to-end correctness

**System Tests**:
- Run on full test set
- Measure all metrics
- Generate visualizations

### Debugging Tips

- **If rule inference fails**: Check VLM prompt, try few-shot examples, validate parsing
- **If state extraction fails**: Visualize extracted state, check image preprocessing, verify parsing
- **If CSP fails**: Print CSP constraints, check for contradictions, verify variable domains
- **If solver times out**: Try simpler puzzle, check constraint propagation, reduce search space

### Code Quality Guidelines

- Use type hints throughout
- Follow PEP 8 style guide
- Keep functions small and focused (<50 lines)
- Use meaningful variable names
- Add comments for complex logic
- Use logging instead of print statements

---

## Expected Timeline

### Week 1: Foundation
- Days 1-2: Project setup, data pipeline, VLM integration
- Days 3-4: Rule inference module
- Days 5-7: State extraction module, initial testing

### Week 2: Core System
- Days 8-10: CSP translation and solving
- Days 11-12: End-to-end integration
- Days 13-14: Initial evaluation on small test set

### Week 3: Experimentation
- Days 15-17: Full evaluation, baseline comparisons
- Days 18-19: Ablation studies
- Days 20-21: Error analysis and debugging

### Week 4: Extensions & Polish
- Days 22-24: Implement one extension
- Days 25-26: Final experiments and analysis
- Days 27-28: Documentation, visualization, writeup preparation

---

## Research Questions to Answer

By the end of this project, you should be able to answer:

1. **Can VLMs learn constraint structures from examples?**
   - Measure: Rule inference accuracy
   - Compare: Different VLM models, different #examples

2. **Does symbolic reasoning (CSP) improve VLM performance?**
   - Measure: VLM+CSP vs Pure VLM accuracy
   - Analyze: When does CSP help? When doesn't it?

3. **Where does the neurosymbolic gap occur?**
   - Error analysis: Perception vs reasoning failures
   - Quantify: Cost of perception errors on solving

4. **How does system scale?**
   - Vary: Puzzle size, complexity, number of constraints
   - Measure: Success rate and runtime

5. **What makes good training examples for rule learning?**
   - Vary: Number, diversity, difficulty of examples
   - Find: Optimal training set composition

---

## Success Criteria

### Minimum Viable Project (B grade):
✅ Working pipeline: Examples → Rules → State → CSP → Solution  
✅ Accuracy >70% on Sudoku test set  
✅ Comparison with pure VLM baseline  
✅ Basic error analysis  
✅ Clean, documented code  

### Strong Project (A grade):
✅ All above +  
✅ Accuracy >85% on Sudoku  
✅ Comprehensive ablation studies  
✅ One research extension implemented  
✅ Publication-quality figures and analysis  
✅ Novel insights about VLM constraint understanding  

### Exceptional Project (A+ / Publication):
✅ All above +  
✅ Multiple puzzle types (generalization)  
✅ Theoretical analysis of neurosymbolic gap  
✅ Novel extension with strong results  
✅ Open-source release with documentation  
✅ Compelling narrative about compositional AI  

---

## Potential Pitfalls & Solutions

### Pitfall 1: VLM Hallucination in Rule Inference
**Problem**: VLM invents rules that don't exist  
**Solution**: 
- Validate rules against all training examples
- Use multiple examples (5+) for consensus
- Implement rule consistency checking

### Pitfall 2: State Extraction Errors
**Problem**: VLM misreads digits, misses cells  
**Solution**:
- Use high-quality, clear images
- Implement confidence scoring
- Add validation checks (e.g., 81 cells for Sudoku)
- Re-query VLM for low-confidence cells

### Pitfall 3: CSP Translation Bugs
**Problem**: Rules not properly converted to CSP constraints  
**Solution**:
- Test translation with hand-crafted rules first
- Verify CSP is well-formed before solving
- Add extensive validation and assertions

### Pitfall 4: Solver Timeout
**Problem**: CSP too complex, solver takes forever  
**Solution**:
- Set reasonable timeouts (60s)
- Use good search heuristics (MRV)
- Consider switching to more efficient solver (MiniZinc)

### Pitfall 5: Evaluation Overfitting
**Problem**: System works on Sudoku but doesn't generalize  
**Solution**:
- Test on multiple puzzle types
- Use diverse image styles in test set
- Implement at least one extension to test generalization

---

## Questions for Human (You) to Decide

Before starting implementation, please decide:

1. **VLM Choice**: Which should be primary?
   - Claude API (easier, faster, costs money)
   - GPT-4V API (alternative)
   - Local LLaVA (free, slower, needs setup)
   - **Recommendation**: Start with Claude API

2. **CSP Solver**: Which library?
   - python-constraint (simpler, good for learning)
   - MiniZinc (more powerful, research-grade)
   - **Recommendation**: Start with python-constraint

3. **Scope**: Just Sudoku or multiple puzzles?
   - Focus deeply on Sudoku (simpler, clearer results)
   - Add Kakuro/KenKen (broader, tests generalization)
   - **Recommendation**: Sudoku first, extensions if time permits

4. **Extension**: Which research extension interests you most?
   - Hierarchical (compositional, fits course)
   - Uncertainty (robust, practical)
   - Interactive (human-in-loop, novel)
   - Multi-puzzle (generalization)
   - **Recommendation**: Hierarchical (best fit for "Compositional AI" course)

5. **Dataset**: Generate or download?
   - Generate synthetic (controllable, fast)
   - Download existing (realistic, already labeled)
   - **Recommendation**: Download existing, then generate variations

---

## Getting Started Checklist

When you're ready to start implementation:

- [ ] Create GitHub repository
- [ ] Set up Python environment (Python 3.10+)
- [ ] Install base dependencies (anthropic, PIL, constraint)
- [ ] Create project structure (folders as specified)
- [ ] Set up API keys in .env file
- [ ] Download/generate initial Sudoku dataset (10-20 images to start)
- [ ] Test VLM API connection with simple query
- [ ] Begin Phase 1: Foundation

**First concrete task**: Implement `VLMInterface` abstract class and `ClaudeVLM` concrete implementation. Test by sending one Sudoku image and getting a response.

---

## Additional Resources

### Relevant Papers
- "Combining Constraint Programming Reasoning with Large Language Model Predictions" (2024)
- "Large Language Models are Neurosymbolic Reasoners" (2024)
- "The Neuro-Symbolic Concept Learner" (2019)

### Useful Libraries
- python-constraint documentation
- Anthropic API documentation
- OpenAI Vision API documentation

### Similar Projects (for inspiration)
- GenCP: Constraint generation with LLMs
- Visual reasoning benchmarks (e.g., CLEVR)
- Program synthesis from examples

---

## Final Notes

This specification is comprehensive but flexible. As you implement:

1. **Follow the phased approach** - don't skip ahead
2. **Test constantly** - verify each component works before integrating
3. **Document as you go** - future you will thank present you
4. **Ask questions** - clarify ambiguities before implementing
5. **Stay focused** - complete core system before fancy extensions

The goal is a **tractable, novel, and scientifically rigorous** project that demonstrates compositional AI principles. Quality over quantity - a well-executed core system beats a half-finished complex system.

Good luck! 🚀