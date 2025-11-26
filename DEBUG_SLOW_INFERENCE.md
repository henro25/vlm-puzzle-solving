# Debugging Slow VLM Inference

Your script is taking 20+ minutes because **VLM inference is very slow**. This guide helps identify why.

## Quick Diagnostics

### 1. Check GPU Status (Run First)

```bash
python check_gpu.py
```

This script shows:
- Is CUDA available?
- GPU name and memory
- GPU computation test

**Save this output** and send it to me.

### 2. Run Inference Speed Debug

```bash
python experiments/debug_inference_speed.py
```

This shows:
- Time for each step (image loading, chat template, generation, etc.)
- GPU memory usage
- Tokens per second
- Whether GPU is being used

**Save the full output** and send it to me.

## What to Look For

### Expected Output (GPU Working)

```
✓ Image loading: 0.123s
✓ Chat template: 0.045s
✓ Input processing: 0.234s
✓ Generation: 3.567s        ← Should be <10s
✓ Decoding: 0.089s
─────────────────────────
✓ EXCELLENT - inference is very fast
Expected end-to-end time per puzzle: 20-30s
```

### Slow Output (GPU Not Working)

```
✓ Generation: 120.000s       ← Over 2 minutes!
⚠ SLOW - inference is slow
Expected end-to-end time per puzzle: 60-120s
or
✗ VERY SLOW - likely CPU-only
```

### GPU Not Available

```
✗ CUDA NOT AVAILABLE - Running on CPU only!
```

## Likely Issues

### Issue 1: CUDA Not Available

**Symptom**: `pytorch version: 2.x.x` but `CUDA available: False`

**Fix**:
```bash
# Reinstall PyTorch with CUDA support
pip uninstall torch torchvision torchaudio -y
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Issue 2: Model Not on GPU

**Symptom**: `Model device: cpu` instead of `cuda:0`

**Possible fix** - Set CUDA_HOME:
```bash
export CUDA_HOME=/usr/local/cuda
python experiments/debug_inference_speed.py
```

### Issue 3: Slow GPU (Older GPU)

**Symptom**: GPU is available and used, but still slow (10-30s per inference)

**This is normal for**:
- Older GPUs (GTX 1080, V100)
- Smaller GPUs (<24GB VRAM)
- Running other heavy workloads on GPU

**Options**:
1. Use a more powerful GPU (A100, H100, RTX 4090)
2. Quantize the model (4-bit, 8-bit)
3. Use a smaller model

## Step-by-Step Debug Process

### 1. First, run GPU check:

```bash
python check_gpu.py > gpu_check.txt 2>&1
```

Then tell me:
- Is CUDA available?
- What GPU do you have?
- How much total VRAM?

### 2. Then, run inference debug:

```bash
python experiments/debug_inference_speed.py > inference_debug.txt 2>&1
```

Then tell me:
- Generation time (e.g., "0.034s" or "120.000s")
- Tokens per second
- Model device
- Peak memory usage

### 3. Monitor GPU during inference:

While step 2 is running, in another terminal:

```bash
watch -n 1 nvidia-smi
```

Tell me:
- Does GPU show `python` process?
- GPU utilization % (should be 80-100%)
- GPU memory used (should increase during generation)

## Analysis Templates

### If GPU is working:

```
GPU: ✓ Available
Generation time: < 10s
Device: cuda:0
GPU Util: 90%+

→ Inference is working optimally
→ 20-40s per puzzle is expected
→ No action needed
```

### If GPU is slow:

```
GPU: ✓ Available
Generation time: 10-60s
Device: cuda:0
GPU Util: 50%+

→ GPU is available but slow
→ Possibly older/smaller GPU
→ Consider quantization or smaller model
```

### If GPU is not being used:

```
GPU: ✓ Available
Generation time: 60+ seconds
Device: cpu
GPU Util: 0%

→ Model is running on CPU!
→ Check CUDA_HOME: echo $CUDA_HOME
→ Set it: export CUDA_HOME=/usr/local/cuda
→ Reinstall PyTorch if needed
```

## Solutions by Scenario

### Scenario A: "CUDA not available"

```bash
# 1. Check if nvidia-smi works
nvidia-smi

# 2. If it works, reinstall PyTorch
pip uninstall torch torchvision torchaudio -y
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 3. Verify
python check_gpu.py
```

### Scenario B: "GPU available but inference still slow"

```bash
# Check GPU during inference
watch -n 1 nvidia-smi

# While watching, run in another terminal:
python experiments/debug_inference_speed.py

# If GPU utilization is 0%, model is on CPU:
export CUDA_HOME=/usr/local/cuda
python experiments/debug_inference_speed.py
```

### Scenario C: "GPU is fast but overall script is slow"

The VLM inference itself is fast, but something else is slow.

Run the verbose test:
```bash
python experiments/test_end_to_end_verbose.py
```

This will show you which phase is slow:
- Model loading
- Rule inference
- State extraction
- CSP solving

## What to Send Me

When you ask for help, please provide:

1. **GPU Check Output**:
   ```bash
   python check_gpu.py
   ```
   Copy the entire output.

2. **Inference Speed Output**:
   ```bash
   python experiments/debug_inference_speed.py
   ```
   Copy the entire output.

3. **GPU Monitoring** (during inference):
   ```bash
   watch -n 1 nvidia-smi
   ```
   Take a screenshot or copy relevant lines showing GPU usage.

4. **System Info**:
   ```bash
   nvidia-smi
   python --version
   torch --version (from python -c "import torch; print(torch.__version__)")
   ```

## Expected Performance Reference

**For Qwen2-VL-7B on different hardware:**

| Hardware | Inference Time | Status |
|----------|-----------------|--------|
| RTX 4090 | 2-5s | Excellent |
| A100 | 3-8s | Excellent |
| RTX 3090 | 5-15s | Good |
| RTX 4070 | 8-20s | Good |
| A10 | 15-30s | Acceptable |
| V100 | 20-40s | Slow |
| CPU (no GPU) | 300+ seconds | Very Slow |

If your time is much higher than listed for your GPU, something is wrong.

## Next Steps

1. Run `python check_gpu.py` and save output
2. Run `python experiments/debug_inference_speed.py` and save output
3. Send me both outputs with your hardware info
4. I'll identify the issue and provide a specific fix

---

**TL;DR**: Run these two commands and send me the output:

```bash
python check_gpu.py > gpu_check.txt
python experiments/debug_inference_speed.py > inference_debug.txt
```

Then tell me what the "Generation time" and "Tokens per second" were.
