# Debugging Instructions for Slow Inference

Since you're running this on a remote machine, here are the exact commands to run and what to send back.

## Quick Start (3 Commands)

Run these 3 commands and send me the output:

```bash
# Command 1: Check GPU
python check_gpu.py

# Command 2: Check if model is on GPU
python check_model_device.py

# Command 3: Detailed inference analysis
python experiments/debug_inference_speed.py
```

**Save all outputs** and send them to me along with:
- Your GPU name (from nvidia-smi)
- Generation time from debug_inference_speed.py
- Whether model device is on GPU or CPU

## Detailed Steps

### Step 1: Basic GPU Check

```bash
python check_gpu.py
```

**Look for:**
- `CUDA available: True` or `False`?
- If True, what GPU name?
- Total memory?

**Expected output if GPU works:**
```
CUDA available: True
CUDA version: 12.1
GPU 0:
  Name: NVIDIA RTX 4090
  Total Memory: 24.0 GB
```

**Expected output if GPU not working:**
```
CUDA available: False
⚠ CUDA NOT AVAILABLE!
```

---

### Step 2: Check If Model Is on GPU

```bash
python check_model_device.py
```

**Look for:**
- `Model device: cuda:0` (good) or `cpu` (bad)?
- GPU memory allocated?
- Generation speed?

**Expected output if model on GPU:**
```
Model device: cuda:0
✓ Model IS on GPU
  GPU Memory:
    - Allocated: 14.5 GB
    - Reserved: 15.0 GB

Quick GPU Test:
  ✓ Generation completed in 3.45s
  ✓ FAST - GPU is working well
```

**Expected output if model on CPU:**
```
Model device: cpu
✗ Model is on CPU (not GPU!)
This is why inference is slow!
```

---

### Step 3: Detailed Inference Analysis

```bash
python experiments/debug_inference_speed.py
```

**This is the most detailed test. Look for:**
- Generation time (the `⏳ GENERATION STARTING` section)
- Tokens per second
- GPU memory usage
- Final assessment (EXCELLENT, GOOD, SLOW, VERY SLOW)

**Expected output if GPU working (fast):**
```
Timing breakdown:
  ✓ Image loading: 0.123s
  ✓ Chat template: 0.045s
  ✓ Input processing: 0.234s
  ✓ Generation: 3.567s          ← Key metric!
  ✓ Decoding: 0.089s

Tokens per second: 143.8

✓ EXCELLENT - inference is very fast (GPU-accelerated)
Expected end-to-end time per puzzle: 20-30s
```

**Expected output if GPU not working (slow):**
```
Timing breakdown:
  ✓ Generation: 120.000s        ← Very slow!

Tokens per second: 4.3

✗ VERY SLOW - likely CPU-only
```

---

## What to Send Me

Please send me:

1. **Full output from all 3 commands** (copy-paste everything)

2. **GPU info** (run this):
   ```bash
   nvidia-smi
   ```
   Send me the output or at least tell me the GPU model and VRAM size.

3. **Key metrics**:
   - From `check_gpu.py`: Is CUDA available?
   - From `check_model_device.py`: Is model on cuda:0 or cpu?
   - From `debug_inference_speed.py`: How long does "Generation" take?

4. **If model is on CPU**: Your CUDA_HOME setting
   ```bash
   echo $CUDA_HOME
   ```

## Common Issues and Quick Fixes

### Issue: Model is on CPU (check_model_device.py shows `cpu`)

**Fix 1: Set CUDA_HOME**
```bash
export CUDA_HOME=/usr/local/cuda
python check_model_device.py  # Try again
```

**Fix 2: Reinstall PyTorch with CUDA**
```bash
pip uninstall torch torchvision torchaudio -y
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
python check_model_device.py  # Try again
```

### Issue: CUDA not available (check_gpu.py shows `False`)

```bash
# Check if nvidia-smi works
nvidia-smi

# If it works, reinstall PyTorch
pip uninstall torch torchvision torchaudio -y
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Verify
python check_gpu.py
```

### Issue: Generation takes 60+ seconds but model is on GPU

Likely causes:
1. GPU is older/slower (V100, older RTX)
2. GPU is busy with other tasks
3. GPU doesn't have enough VRAM (causing spillover to CPU)

**Check GPU memory usage during inference:**
```bash
# Terminal 1: Run inference
python experiments/debug_inference_speed.py

# Terminal 2: Watch GPU (in another terminal)
watch -n 1 nvidia-smi
```

Look for:
- Does GPU memory increase during generation?
- GPU utilization % (should be 80%+)
- Any OOM errors in the logs?

---

## Expected Timeline

**If GPU is working:**
- Model load: 5-10s
- Rule inference: 5-15s (with optimizations)
- Rest: 5-10s
- **Total: 20-40s per puzzle**

**If GPU is not working (CPU only):**
- Model load: 5-10s
- Rule inference: 120-300s (CPU is very slow!)
- Rest: 5-10s
- **Total: 130-320s per puzzle** (2+ minutes!)

**What you're seeing now (20+ minutes):**
- Likely CPU-only inference
- Probably 120+ seconds per step

---

## After You Run These Tests

Come back with:
1. All 3 command outputs
2. Key metrics (generation time, tokens/sec)
3. Your hardware (GPU model, VRAM)

I'll be able to tell you:
- Whether GPU is being used
- Why inference is slow (if it is)
- Specific fixes to apply

---

## Files You'll Be Running

- `check_gpu.py` - Quick GPU status check
- `check_model_device.py` - Check if model is on GPU and test inference speed
- `experiments/debug_inference_speed.py` - Detailed breakdown of each inference step

All output goes to console (can copy-paste or redirect to file).

---

## Command to Save Output to Files

If you want to save outputs to files:

```bash
python check_gpu.py > gpu_check.txt 2>&1
python check_model_device.py > model_device.txt 2>&1
python experiments/debug_inference_speed.py > inference_debug.txt 2>&1
nvidia-smi > nvidia_smi.txt

# Then check them:
cat gpu_check.txt
cat model_device.txt
cat inference_debug.txt
cat nvidia_smi.txt
```

---

## TL;DR

Run these 3 commands right now:

```bash
python check_gpu.py
python check_model_device.py
python experiments/debug_inference_speed.py
```

Send me the output and tell me:
- Generation time?
- Model device (cuda or cpu)?
- GPU name and VRAM?

I'll fix it!
