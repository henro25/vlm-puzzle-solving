# Quick Debug Reference

## TL;DR

If `test_end_to_end.py` seems stuck after checkpoint loading:

1. **It's probably not stuck** - VLM inference takes 10-30 seconds
2. **To verify**: Run `python experiments/test_vlm_inference_only.py`
3. **To see progress**: Run `python experiments/test_end_to_end_verbose.py`

## 3-Minute Debug Checklist

- [ ] Run: `python experiments/test_vlm_inference_only.py`
  - If completes in <30s: Script is working normally
  - If hangs: Check GPU/CPU with `nvidia-smi`

- [ ] Check GPU: `nvidia-smi`
  - Should show Python process using ~15GB VRAM
  - If nothing: Model running on CPU (very slow, 1-2min per puzzle)

- [ ] Run verbose: `python experiments/test_end_to_end_verbose.py`
  - See exact timing for each phase
  - See where most time is spent

## Expected Timeline

```
Total time: 30-60 seconds per puzzle

Breakdown:
├─ Model load:     15-20s
├─ Model to GPU:    5-10s (looks stuck, but working)
├─ VLM inference:  10-30s (mostly here)
├─ CSP solving:    0.1-1s
└─ Everything else: 2-5s
```

## Is It Actually Stuck?

**Run this command**:
```bash
timeout 120 python experiments/test_vlm_inference_only.py
```

- **Completes in <30s**: Working normally ✓
- **Hangs and kills at 120s**: Actually stuck ✗

## Common Scenarios

### Scenario 1: First run takes long, subsequent runs are fast
- **Cause**: Model caching first time
- **Expected**: Normal
- **Action**: None needed

### Scenario 2: Hangs after "Loading checkpoint shards"
- **Cause**: Could be moving to GPU or starting inference
- **Solution**: Run `test_vlm_inference_only.py` to see
- **If <30s**: Normal
- **If >30s**: Likely CPU-only

### Scenario 3: "No solution found" message
- **Cause**: CSP solver couldn't find solution with given rules
- **Solution**: Check rule inference quality
- **Action**: Run `debug_csp_structure.py`

### Scenario 4: GPU memory error ("CUDA out of memory")
- **Cause**: Not enough VRAM
- **Solution**:
  - Close other GPU apps
  - Use float32: edit `src/models/qwen_model.py` precision
  - Use CPU instead (slow)

## One-Command Tests

```bash
# Test if VLM inference works
python experiments/test_vlm_inference_only.py

# Test full end-to-end with timing
python experiments/test_end_to_end_verbose.py

# See CSP structure and solver comparison
python experiments/debug_csp_structure.py

# Compare different solvers
python experiments/compare_solvers.py

# Watch GPU while running
watch nvidia-smi  # In another terminal
```

## What "Slow" Looks Like

### Normal (GPU-enabled)
```
✓ Inference completed in 12.45s
✓ Model loaded in 15.23s
✓ Total time: 27.68s per puzzle
→ This is expected!
```

### Slow (CPU-only)
```
✗ Inference completed in 120+ seconds
✓ Model loaded in 15s
✗ Total time: 2+ minutes per puzzle
→ GPU not being used
→ Check: nvidia-smi should show GPU usage
```

## Key Files for Debugging

| File | Shows |
|------|-------|
| `DEBUGGING_TOOLS.md` | Detailed guide |
| `DEBUG_HANGING_SCRIPT.md` | Full explanation with examples |
| `src/models/qwen_model.py` | VLM loading & inference logs |
| `experiments/test_vlm_inference_only.py` | VLM speed test |
| `experiments/test_end_to_end_verbose.py` | Phase-by-phase timing |

## Next Steps

1. **Identify bottleneck**: Run `test_vlm_inference_only.py`
2. **See breakdown**: Run `test_end_to_end_verbose.py`
3. **If CSP solving issue**: Run `debug_csp_structure.py`
4. **Still confused?**: Check `DEBUG_HANGING_SCRIPT.md`

---

**Bottom line**: Most pauses are expected. Use the test scripts to verify.
