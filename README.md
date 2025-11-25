# Visual Constraint Discovery: Neurosymbolic Puzzle Solving

A research project exploring how Vision-Language Models can inductively learn constraint structures from visual examples, then use CSP solvers to solve new puzzles.

## Overview

**Research Question**: Can VLMs learn constraint rules from visual examples and apply them to solve new constraint satisfaction problems?

### System Pipeline

```
Solved Examples → VLM Rule Inference → Inferred Rules
                                              ↓
                                    New Puzzle Image
                                              ↓
                                    VLM State Extraction
                                              ↓
                                      Puzzle State
                                              ↓
                                    CSP Translation
                                              ↓
                                      CSP Problem
                                              ↓
                                      CSP Solver
                                              ↓
                                          Solution
```

## Project Status

- ✅ **Phase 1**: Foundation & Infrastructure (Complete)
  - Project structure created
  - Configuration system
  - VLM interface (Qwen2-VL)
  - Core data structures
  - Dataset management

- 🚀 **Phase 2**: Rule Inference Module (In Progress)
  - Prompt templates
  - Rule parser
  - RuleInferenceModule

- ✅ **Phase 3**: State Extraction Module (Complete)
  - VLM-based cell value extraction
  - JSON parsing with error recovery
  - State validation and confidence scoring

- ✅ **Phase 4**: CSP Translation & Solving (Complete)
  - Rule-to-CSP translation
  - Optimized python-constraint solver (15-60x speedup)
  - Fast OR-Tools solver (150-600x speedup over original)
  - Automatic solver selection with fallback
  - Performance diagnostics tools

- ⏳ **Phase 5-6**: Evaluation, analysis, hierarchical extensions

## Quick Start

### 1. Setup Environment

```bash
# Clone and navigate to project
git clone git@github.com:henro25/vlm-puzzle-solving.git
cd vlm-puzzle-solving

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure .env
cp .env.example .env
# Edit .env as needed
```

### 2. Download & Prepare Dataset

See [Dataset Setup](#dataset-setup) section below.

### 3. Test VLM Connection

```bash
python -c "
from src.models.qwen_model import QwenVLModel
from src.config import init_config
from src.utils.logging import setup_logging

# Initialize
init_config()
setup_logging()

# Test model
vlm = QwenVLModel()
vlm.load_model()
print('✓ Model loaded successfully')
vlm.unload_model()
"
```

### 4. Run First Experiment

```bash
python -m experiments.quick_test
```

## Dataset Setup

### Option A: Download from Kaggle (Recommended)

**TODO**: Follow these steps to download and prepare Sudoku dataset:

```bash
# 1. Install kaggle CLI
pip install kaggle

# 2. Set up Kaggle credentials
# Go to https://www.kaggle.com/settings/account
# Download your API token (kaggle.json)
# The kaggle.json should be in this form:
# {
#  "username": "your_kaggle_username",
#  "key": "your_api_key"
#}
# Place in ~/.kaggle/kaggle.json
# chmod 600 ~/.kaggle/kaggle.json

# 3. Download 1 million Sudoku puzzles dataset
kaggle datasets download -d bryanpark/sudoku

# 4. Extract
mkdir data
unzip sudoku.zip -d data/raw/

# 5. Prepare dataset (convert to images)
python scripts/prepare_sudoku_kaggle.py data/raw/sudoku.csv

# Expected output:
# data/raw/sudoku/
# ├── solved/
# │   ├── solved_001.png
# │   ├── solved_001.json
# │   ├── solved_002.png
# │   ├── solved_002.json
# │   └── ... (100 training examples)
# └── unsolved/
#     ├── unsolved_001.png
#     ├── unsolved_001.json
#     ├── unsolved_002.png
#     ├── unsolved_002.json
#     └── ... (200 test puzzles)
```

### Option B: Generate Synthetic Dataset

```bash
# Generate 100 solved + 200 unsolved Sudoku puzzles with images
python scripts/generate_synthetic_sudoku.py --num-solved 100 --num-unsolved 200

# This creates:
# - Random valid Sudoku puzzles
# - Renders them as images (448x448 PNG)
# - Generates ground truth JSON with initial state and solution
# - Includes difficulty levels
```

### Option C: Quick Test Dataset (5 puzzles)

```bash
# For quick testing without full dataset download
python scripts/generate_synthetic_sudoku.py --num-solved 5 --num-unsolved 5 --quick
```

## Project Structure

```
visual-constraint-discovery/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── .env.example                       # Environment template
├── .gitignore                         # Git ignore rules
│
├── src/
│   ├── __init__.py
│   ├── config.py                      # Configuration management
│   │
│   ├── core/                          # Core data structures
│   │   ├── constraint_rules.py        # ConstraintRule, ConstraintRuleSet
│   │   ├── puzzle_state.py            # PuzzleState representation
│   │   └── csp_problem.py             # CSP problem definition
│   │
│   ├── data/                          # Data pipeline
│   │   ├── dataset.py                 # SudokuDataset class
│   │   └── loaders.py                 # Data loading functions
│   │
│   ├── models/                        # VLM implementations
│   │   ├── vlm_interface.py           # Abstract base class
│   │   └── qwen_model.py              # Qwen2-VL implementation
│   │
│   ├── modules/                       # Core system modules
│   │   ├── rule_inference.py          # Rule inference pipeline
│   │   ├── state_extraction.py        # State extraction pipeline
│   │   └── csp_translator.py          # Rules + state → CSP
│   │
│   ├── solvers/                       # CSP solvers
│   │   └── csp_solver.py              # CSP solving
│   │
│   ├── prompts/                       # Prompt templates
│   │   ├── rule_inference_prompts.py
│   │   └── state_extraction_prompts.py
│   │
│   ├── parsers/                       # Output parsing
│   │   ├── rule_parser.py
│   │   └── state_parser.py
│   │
│   ├── evaluation/                    # Evaluation & metrics
│   │   ├── metrics.py
│   │   ├── evaluator.py
│   │   └── error_analysis.py
│   │
│   ├── visualization/                 # Plotting
│   │   └── plot_results.py
│   │
│   ├── utils/                         # Utilities
│   │   ├── logging.py
│   │   └── image_processing.py
│   │
│   └── extensions/                    # Research extensions
│       └── hierarchical.py            # Hierarchical constraint discovery
│
├── data/
│   ├── raw/sudoku/
│   │   ├── solved/                    # Solved examples (for rule learning)
│   │   └── unsolved/                  # Test puzzles
│   ├── processed/                     # Cached/processed data
│   └── ground_truth/                  # Ground truth labels
│
├── scripts/                           # Utility scripts
│   ├── prepare_sudoku_kaggle.py       # Convert Kaggle CSV → images
│   └── generate_synthetic_sudoku.py   # Generate synthetic puzzles
│
├── experiments/                       # Experiment runners
│   ├── quick_test.py                  # Quick sanity check
│   ├── run_baseline.py                # Baseline comparisons
│   ├── run_main_experiment.py         # Full evaluation
│   └── run_ablation.py                # Ablation studies
│
├── notebooks/                         # Jupyter notebooks
│   ├── 01_data_exploration.ipynb
│   ├── 02_rule_inference_test.ipynb
│   ├── 03_state_extraction_test.ipynb
│   └── 04_results_analysis.ipynb
│
├── tests/                             # Unit tests
│   ├── test_rule_inference.py
│   ├── test_state_extraction.py
│   ├── test_csp_solver.py
│   └── test_integration.py
│
└── results/                           # Experiment outputs
    ├── figures/                       # Visualization plots
    ├── metrics/                       # Quantitative results
    └── logs/                          # Experiment logs
```

## Configuration

Edit `.env` to customize:

```bash
# VLM settings
VLM_MODEL=Qwen/Qwen2-VL-7B-Instruct
DEVICE=cuda  # or cpu

# Paths
DATA_DIR=./data
RESULTS_DIR=./results

# Logging
LOG_LEVEL=INFO

# Seed
SEED=42
```

## Key Components

### VLM Interface

All VLM models inherit from `VLMInterface`:

```python
from src.models.qwen_model import QwenVLModel

# Single query
vlm = QwenVLModel()
vlm.load_model()
response = vlm.query("image.png", "What rules apply here?")
print(response.text)

# Batch queries
responses = vlm.batch_query(
    images=["img1.png", "img2.png"],
    prompts="Extract the Sudoku state"
)

vlm.unload_model()
```

### Core Data Structures

**PuzzleState**: Represents puzzle configuration
```python
from src.core.puzzle_state import PuzzleState

state = PuzzleState(
    grid_size=(9, 9),
    filled_cells={(0, 0): 5, (0, 1): 3},
    domains={(0, 2): [1, 2, 4, 6, 7, 8, 9]}
)
```

**ConstraintRuleSet**: Inferred rules
```python
from src.core.constraint_rules import ConstraintRuleSet, ConstraintRule

rules = ConstraintRuleSet()
rules.add_rule(ConstraintRule(
    constraint_type="all_different",
    scope=["row_0"],
    description="All values in row 0 must be different"
))
```

**CSPProblem**: Formal constraint problem
```python
from src.core.csp_problem import CSPProblem

csp = CSPProblem()
csp.add_variable("cell_00", domain=[1, 2, 3, 4, 5, 6, 7, 8, 9])
csp.add_constraint("row_constraint", scope=["cell_00", "cell_01"], ...)
```

## Running Experiments

### 1. Quick Test (5 puzzles)
```bash
python -m experiments.quick_test
```

### 2. Main Experiment (100 test puzzles)
```bash
python -m experiments.run_main_experiment
```

### 3. Baseline Comparison (VLM only vs VLM+CSP)
```bash
python -m experiments.run_baseline
```

### 4. Ablation Studies (varying # of examples)
```bash
python -m experiments.run_ablation
```

## Expected Results

Success criteria:
- **>70%** end-to-end solving success on test set (B grade)
- **>85%** success (A grade)
- **Comprehensive analysis** of failures and extensions

## Contributing

### Code Style
- Follow PEP 8
- Use type hints
- Write docstrings
- Use logging, not print()

### Testing
```bash
# Run unit tests
pytest tests/

# Run with coverage
pytest --cov=src tests/
```

## Known Limitations & TODOs

### Dataset Preparation
- [ ] Verify Kaggle download works with updated API
- [ ] Test CSV → image conversion handles all edge cases
- [ ] Add support for other puzzle types (Kakuro, KenKen)

### VLM Integration
- [ ] Test Qwen2-VL memory usage with large batches
- [ ] Verify GPU memory optimization
- [ ] Add fallback to CPU if CUDA unavailable

### Rule Inference
- [ ] Implement confidence scoring for inferred rules
- [ ] Add rule validation against training set
- [ ] Handle conflicting rules

### State Extraction
- [ ] Add OCR fallback for unclear digits
- [ ] Implement cell confidence scoring
- [ ] Test on rotated/skewed images

### CSP Solving
- [ ] Benchmark constraint propagation performance
- [ ] Add timeout recovery mechanisms
- [ ] Implement heuristic selection

### Evaluation
- [ ] Create publication-quality visualizations
- [ ] Implement comparative baseline analysis
- [ ] Add error categorization

### Extensions
- [ ] Implement hierarchical constraint discovery
- [ ] Add uncertainty-aware solving
- [ ] Build interactive verification loop

## Performance Notes

- **VLM Loading**: ~30-45 seconds (first time)
- **Inference per puzzle**: ~2-5 seconds (Qwen2-VL-7B)
- **CSP Solving**: 50-200ms with OR-Tools (optimized), <1s with optimized python-constraint
  - Bottleneck: Rule inference and VLM inference (not CSP solving)
  - See [Phase 4 Optimizations](PHASE4_OPTIMIZATIONS.md) for solver selection
- **GPU Memory**: ~15GB for Qwen2-VL-7B (float16)

### CSP Solver Performance

The system uses **Google OR-Tools** by default for 5-100x speedup:

```python
# Automatic solver selection (OR-Tools if available, fallback to python-constraint)
solver = PuzzleSolver(vlm)

# Or explicitly choose solver
solver = PuzzleSolver(vlm, csp_solver_backend="ortools")  # Fast
solver = PuzzleSolver(vlm, csp_solver_backend="constraint")  # Compatible
```

**Benchmark Results**:
| Solver | Time | Speedup |
|--------|------|---------|
| python-constraint (original) | 30+ seconds | 1x |
| python-constraint (optimized) | 0.5-2s | 15-60x |
| OR-Tools | 0.05-0.2s | 150-600x |

For performance diagnostics and solver comparison, see:
- `experiments/diagnose_csp_performance.py` - Performance analysis
- `experiments/compare_solvers.py` - Solver comparison

## References

- **Specification**: See `VISUAL_CONSTRAINT_DISCOVERY_SPEC.md`
- **Qwen2-VL Docs**: https://huggingface.co/Qwen/Qwen2-VL-7B-Instruct
- **python-constraint**: https://pypi.org/project/python-constraint/
- **Sudoku Dataset**: https://www.kaggle.com/datasets/bryanpark/sudoku

## License

Educational research project for CS course.

---

**Questions or issues?**
Check the TODOs in this README or review `VISUAL_CONSTRAINT_DISCOVERY_SPEC.md` for implementation details.
