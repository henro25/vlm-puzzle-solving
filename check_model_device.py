#!/usr/bin/env python
"""Check if model is actually on GPU."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.config import init_config
from src.utils.logging import setup_logging
from src.models.qwen_model import QwenVLModel
import torch

print("=" * 70)
print("MODEL DEVICE CHECK")
print("=" * 70)

print(f"\n[1] System Info:")
print(f"  CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"  GPU: {torch.cuda.get_device_name(0)}")
    print(f"  CUDA_HOME: {torch.cuda.get_device_properties(0)}")

init_config()
setup_logging()

print(f"\n[2] Loading model...")
vlm = QwenVLModel()
vlm.load_model()

print(f"\n[3] Model Device Info:")
print(f"  Model device: {vlm.model.device}")
print(f"  Model dtype: {vlm.model.dtype}")

# Check if on GPU
if "cuda" in str(vlm.model.device):
    print(f"  ✓ Model IS on GPU")
    print(f"\n  GPU Memory:")
    print(f"    - Allocated: {torch.cuda.memory_allocated() / 1e9:.1f} GB")
    print(f"    - Reserved: {torch.cuda.memory_reserved() / 1e9:.1f} GB")
    print(f"    - Available: {(torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated()) / 1e9:.1f} GB")
else:
    print(f"  ✗ Model is on CPU (not GPU!)")
    print(f"  This is why inference is slow!")

# Test GPU inference
print(f"\n[4] Quick GPU Test:")
try:
    from src.data.loaders import load_training_examples
    examples = load_training_examples(num_examples=1)
    if examples:
        example = examples[0]
        from src.utils.image_processing import load_image
        image = load_image(example.image_path)

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": "Briefly describe this image."},
                ],
            }
        ]

        text = vlm.processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        inputs = vlm.processor(
            text=text,
            images=[image],
            padding=True,
            return_tensors="pt",
        ).to(vlm.model.device)

        print(f"  Starting generation...")
        import time
        start = time.time()

        with torch.no_grad():
            output_ids = vlm.model.generate(
                **inputs,
                max_new_tokens=64,
                do_sample=False,
                num_beams=1,
            )

        elapsed = time.time() - start
        print(f"  ✓ Generation completed in {elapsed:.2f}s")
        print(f"  Generated {output_ids.shape[1]} tokens")
        print(f"  Speed: {output_ids.shape[1] / elapsed:.1f} tokens/sec")

        if elapsed < 5:
            print(f"  ✓ FAST - GPU is working well")
        elif elapsed < 30:
            print(f"  ⚠ SLOW - GPU may be struggling")
        else:
            print(f"  ✗ VERY SLOW - Check if model is actually on GPU")

except Exception as e:
    print(f"  ✗ Test failed: {e}")
    import traceback
    traceback.print_exc()

vlm.unload_model()

print("\n" + "=" * 70)
