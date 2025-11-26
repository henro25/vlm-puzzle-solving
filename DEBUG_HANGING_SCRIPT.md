# Debugging: Script Hanging/Pausing

## What You're Seeing

When running `test_end_to_end.py`, you see:

```
Loading checkpoint shards:   0%|          | 0/5 [00:00<?, ?it/s]
Loading checkpoint shards:  20%|██        | 1/5 [00:02<00:09,  2.34s/it]
Loading checkpoint shards:  40%|████      | 2/5 [00:04<00:06,  2.29s/it]
Loading checkpoint shards:  60%|██████    | 3/5 [00:06<00:04,  2.27s/it]
Loading checkpoint shards:  80%|████████  | 4/5 [00:09<00:02,  2.26s/it]
Loading checkpoint shards: 100%|██████████| 5/5 [00:09<00:00,  1.68s/it]
```

Then it pauses...

## What's Happening

### Phase 1: Loading Model (Expected: 10-20 seconds)
- This is **normal** - it's loading 5 checkpoint shards from HuggingFace
- Each shard is ~2GB, takes 2-3 seconds each
- Moving model to GPU takes additional time
- This is expected and you should see progress bars

### Phase 2: After Loading (May pause here)
After the checkpoint loading completes, you may see a pause. This is likely:

1. **Moving model to VRAM** (if using GPU)
   - Takes 5-15 seconds depending on GPU speed
   - No progress bar shown during this phase

2. **Loading processor**
   - Smaller, usually <1 second
   - Shown in logs as: `"→ Loading processor..."`

3. **First inference**
   - This can take 10-30 seconds because:
     - Model is warming up
     - First token generation is slowest
     - Subsequent inferences are faster

## How to Debug

### Run Verbose Version (Shows Detailed Progress)

```bash
python experiments/test_end_to_end_verbose.py
```

This shows:
- Which phase is currently running
- Timing for each phase
- Where exactly it's stuck

### Enable Debug Logging

Set log level to DEBUG in `src/config.py`:

```python
logging.log_level = "DEBUG"
```

Or run with debug logging:

```bash
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
exec(open('experiments/test_end_to_end.py').read())
"
```

### Check GPU Memory

If it hangs while "Moving model to CUDA", you may have GPU memory issues:

```bash
nvidia-smi  # Watch GPU memory usage
```

If VRAM is full, try:
- Close other GPU-using applications
- Use float32 instead of float16 (slower but uses less memory)
- Use CPU instead of GPU (much slower)

## Expected Timeline

| Phase | Duration | What's Happening |
|-------|----------|------------------|
| Load config | <1s | Reading config files |
| Load data | 1-2s | Loading puzzle dataset |
| Initialize VLM | - | - |
| - Load model checkpoint | 10-15s | ✓ Progress bar shown |
| - Move to GPU | 5-10s | No progress bar, may look stuck |
| - Load processor | 1s | ✓ Progress message shown |
| **Rule Inference** | **10-30s** | **Most time spent here** |
| - Prepare images | 1-2s | Loading puzzle images |
| - VLM inference | 8-25s | Model generating rules (GPU/CPU dependent) |
| - Parse response | 1s | Converting JSON to rules |
| State Extraction | 1-5s | (Using ground truth, minimal work) |
| CSP Translation | 1-2s | Converting rules to constraints |
| CSP Solving | 0.1-1s | Solving puzzle |
| **Total** | **30-60s** | **Per puzzle** |

## If Script Seems Stuck

### Check These in Order

1. **Is there output every 10-20 seconds?**
   - If yes: script is working, just slow (expected)
   - If no: might be actually stuck

2. **Watch GPU memory** (if using GPU)
   ```bash
   watch nvidia-smi
   ```
   - Should see memory increase as model loads
   - Should see GPU utilization during inference

3. **Check system resources**
   ```bash
   top  # CPU usage
   htop  # Memory usage
   ```

4. **Run verbose version** to see exact phase:
   ```bash
   python experiments/test_end_to_end_verbose.py
   ```

5. **Try debug mode** with timeout:
   ```bash
   timeout 120 python experiments/test_end_to_end_verbose.py
   ```
   - If process gets killed at 120s, it's definitely hanging
   - If it completes, it's just slow

## Common Issues & Solutions

### 1. "No output for 5+ minutes"
**Likely**: GPU memory issue or dataset not loaded
**Solution**:
```bash
python experiments/test_end_to_end_verbose.py  # See where it stops
```

### 2. "Loading checkpoint shards" progress stalls
**Likely**: Network issue downloading model
**Solution**: Check internet connection, or pre-download model:
```bash
python -c "from transformers import Qwen2VLForConditionalGeneration; Qwen2VLForConditionalGeneration.from_pretrained('Qwen/Qwen2-VL-7B-Instruct')"
```

### 3. "OutOfMemory" error
**Likely**: GPU doesn't have enough VRAM
**Solution**: Use float32 or CPU (edit `src/models/qwen_model.py`)

### 4. "Takes >120s for single puzzle"
**Likely**: CPU-only inference (very slow) or GPU bottleneck
**Solution**: Check device in logs, ensure using GPU

## What You Should See

**Expected successful run output:**
```
[1/5] Initializing config...
[2/5] Loading data...
  ✓ Loaded 3 training examples, 1 test puzzles
[3/5] Initializing VLM...
  → Loading checkpoint shards...
  [progress bars...]
  → Moving model to cuda...
  → Loading processor...
  ✓ Model loaded in 15.3s
[4/5] Creating puzzle solver...
  ✓ Solver initialized (backend: constraint)
[5/5] Solving puzzles (using ground truth state)...
  Puzzle: unsolved_164
  Image: data/raw/sudoku/unsolved/unsolved_164.png
    → Calling solver...
    ✓ Puzzle solved in 0.15s!
```

## Next Steps

1. **Run verbose version to identify exact bottleneck:**
   ```bash
   python experiments/test_end_to_end_verbose.py
   ```

2. **If it hangs somewhere specific**, let me know which phase and I can add more detailed debugging to that component

3. **Check the logs:**
   ```bash
   tail -f logs/latest.log
   ```

## Summary

- Checkpoint loading (with progress bar) is **normal**
- Pause after that is **normal** (moving to GPU)
- Total 30-60 seconds per puzzle is **expected**
- Use verbose script to find actual bottleneck
- Script is not "stuck", just slow (normal for VLM inference)
