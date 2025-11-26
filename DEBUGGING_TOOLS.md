# Debugging Tools for Phase 4

When the end-to-end test seems to "pause" or "hang", use these tools to identify where time is being spent.

## Quick Answer

The pause you're seeing after "Loading checkpoint shards" is **normal** - it's:
1. Moving the model from CPU to GPU (~5-15 seconds)
2. Loading the processor (~1 second)
3. Starting the first VLM inference (8-25 seconds)

**Total expected time: 30-60 seconds per puzzle** (mostly VLM inference)

## Debugging Tools

### 1. Test VLM Inference Speed (RECOMMENDED)

**What it does**: Measures how fast VLM inference is in isolation

```bash
python experiments/test_vlm_inference_only.py
```

**Output**:
```
Inference completed in 12.45s
Response length: 1235 chars
Tokens generated: 145
Throughput: 11.6 tokens/sec

Model load time: 15.23s
Inference time: 12.45s
Total time: 27.68s
```

**Interpretation**:
- **<5s inference**: GPU is working great
- **5-15s inference**: Normal speed
- **>30s inference**: Likely CPU-only (slow)

### 2. Test End-to-End with Detailed Output

**What it does**: Shows timing for each phase

```bash
python experiments/test_end_to_end_verbose.py
```

**Output**:
```
[1/5] Initializing config...
[2/5] Loading data...
  ✓ Loaded 3 training examples, 1 test puzzles
[3/5] Initializing VLM...
  → Loading checkpoint shards...
  ✓ Model loaded in 16.4s
[4/5] Creating puzzle solver...
  ✓ Solver initialized (backend: constraint)
[5/5] Solving puzzles (using ground truth state)...
  Puzzle: unsolved_164
    → Calling solver...
    ✓ Puzzle solved in 0.15s!
```

**Tells you**: Which phase is consuming time

### 3. Enable Debug Logging

**What it does**: Shows detailed logs of what's happening internally

**Option A**: Set environment variable
```bash
LOGLEVEL=DEBUG python experiments/test_end_to_end.py
```

**Option B**: Edit `src/config.py`
```python
# Change log_level from "INFO" to "DEBUG"
logging.log_level = "DEBUG"
```

**Option C**: Run with Python debug
```bash
python -u -m pdb experiments/test_end_to_end.py
```

**What you'll see**:
- Each step of model loading
- Image loading details
- VLM query details
- Constraint solving steps

### 4. Monitor GPU Usage

**Check GPU memory and utilization while script runs**:

```bash
# Terminal 1: Run test
python experiments/test_end_to_end.py

# Terminal 2: Monitor GPU
watch -n 1 nvidia-smi
```

**What to look for**:
- GPU memory should increase during model load (to ~15GB)
- GPU utilization should spike during inference
- If memory stays low during "pause", model might be on CPU

### 5. Performance Diagnostics

**Detailed CSP structure analysis**:

```bash
python experiments/debug_csp_structure.py
```

**Shows**:
- CSP variable and constraint statistics
- Comparison of python-constraint vs OR-Tools solvers
- Where time is spent in solving

### 6. Solver Comparison

**Compare solver performance**:

```bash
python experiments/compare_solvers.py
```

**Shows**:
- Time comparison between solvers
- Success rates
- Speedup metrics

## Expected Timing Breakdown

For a typical run:

```
Model Loading:           15-20s ✓ (shown with progress bar)
Moving to GPU:            5-10s (looks like pause, no output)
Rule Inference:          10-30s (longest phase, VLM inference)
  - Image loading:         1-2s
  - VLM inference:         8-25s (depends on GPU vs CPU)
  - JSON parsing:          1-2s
State Extraction:         1-5s (minimal with ground truth)
CSP Translation:          1-2s
CSP Solving:              0.1-1s (fast)
─────────────────────────────────
TOTAL:                   30-60s per puzzle
```

## Troubleshooting Guide

### Script produces no output for 2+ minutes

1. **Check if process is alive**:
   ```bash
   ps aux | grep python
   ```

2. **Run verbose version to see progress**:
   ```bash
   python experiments/test_end_to_end_verbose.py
   ```

3. **Run inference-only test**:
   ```bash
   python experiments/test_vlm_inference_only.py
   ```

### GPU is not being used

Check logs for:
```
Loading without device_map, will move to device manually
```

This means GPU might not be available. Verify:
```bash
python -c "import torch; print(f'GPU available: {torch.cuda.is_available()}'); print(f'Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"CPU\"}')"
```

### Inference is very slow (>30s per puzzle)

Likely causes:
1. **Running on CPU** instead of GPU
   - Check: `nvidia-smi` shows no Python process
   - Fix: Install CUDA, check GPU driver

2. **GPU memory is full**
   - Check: `nvidia-smi` shows high memory usage
   - Fix: Close other GPU programs, restart script

3. **Network issue downloading model**
   - Check: First time running, "Loading checkpoint shards" hangs
   - Fix: Check internet, try again, or pre-download model

## Scripts Created for Debugging

| Script | Purpose | When to Use |
|--------|---------|------------|
| `test_vlm_inference_only.py` | Measures VLM inference speed | Identify if VLM is slow |
| `test_end_to_end_verbose.py` | Shows timing for each phase | See where time goes |
| `debug_csp_structure.py` | Analyzes CSP and solvers | Debug solving issues |
| `compare_solvers.py` | Compares solver performance | Benchmark different solvers |
| `diagnose_csp_performance.py` | Detailed CSP analysis | Understand CSP structure |

## Enhanced Logging

Added detailed logging to:
- `src/models/qwen_model.py`: Model loading and inference steps
- Log messages show:
  - Model loading progress
  - Image processing
  - Input preparation
  - Token generation
  - Response decoding

## Summary

If script seems to "hang":

1. **First**: Run `test_vlm_inference_only.py` to measure baseline VLM speed
2. **Second**: Run `test_end_to_end_verbose.py` to see per-phase timing
3. **Third**: Check GPU with `nvidia-smi` while script runs
4. **Finally**: Enable DEBUG logging if still unclear

**Most likely**: Script is not hanging, just doing VLM inference which takes 10-30 seconds.
