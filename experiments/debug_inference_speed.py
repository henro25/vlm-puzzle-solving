#!/usr/bin/env python
"""Debug VLM inference speed - detailed performance analysis."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import init_config, config
from src.utils.logging import setup_logging, get_logger
from src.data.loaders import load_training_examples
from src.models.qwen_model import QwenVLModel

logger = get_logger(__name__)


def main():
    """Test VLM inference speed with detailed diagnostics."""
    print("=" * 80)
    print("VLM INFERENCE SPEED DEBUG")
    print("=" * 80)

    # Initialize
    init_config()
    setup_logging(config().logging.log_dir, config().logging.log_level)

    # Load data
    print("\n[1] Loading training examples...")
    try:
        examples = load_training_examples(num_examples=1)
        if not examples:
            print("✗ No examples loaded")
            return
        print(f"✓ Loaded {len(examples)} example")
    except Exception as e:
        print(f"✗ Failed to load data: {e}")
        return

    # Initialize VLM
    print("\n[2] Loading VLM model...")
    vlm = QwenVLModel()

    start = time.time()
    vlm.load_model()
    load_time = time.time() - start
    print(f"✓ Model loaded in {load_time:.2f}s")

    # Check device
    print(f"\n[3] Device Information:")
    import torch
    print(f"  - CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"  - Device name: {torch.cuda.get_device_name(0)}")
        print(f"  - Device capability: {torch.cuda.get_device_capability(0)}")
        print(f"  - Total memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
    print(f"  - Model device: {vlm.model.device}")
    print(f"  - Model dtype: {vlm.model.dtype}")

    # Check GPU memory before inference
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()
        print(f"  - Memory before inference: {torch.cuda.memory_allocated() / 1e9:.1f} GB")

    # Test inference
    print(f"\n[4] Testing VLM inference...")
    example = examples[0]

    from src.prompts.rule_inference_prompts import get_rule_inference_prompt

    prompt = get_rule_inference_prompt(num_examples=1)
    print(f"  - Prompt length: {len(prompt)} chars")
    print(f"  - Image path: {example.image_path}")

    try:
        print(f"\n  Starting inference at {time.strftime('%H:%M:%S')}...")
        start_time = time.time()

        # Time each step
        print(f"\n  Timing breakdown:")

        # Step 1: Image loading
        step_start = time.time()
        from src.utils.image_processing import load_image
        image = load_image(example.image_path)
        step_time = time.time() - step_start
        print(f"    ✓ Image loading: {step_time:.3f}s")

        # Step 2: Message preparation
        step_start = time.time()
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": prompt},
                ],
            }
        ]
        step_time = time.time() - step_start
        print(f"    ✓ Message preparation: {step_time:.3f}s")

        # Step 3: Chat template
        step_start = time.time()
        text = vlm.processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        step_time = time.time() - step_start
        print(f"    ✓ Chat template: {step_time:.3f}s")

        # Step 4: Input processing
        step_start = time.time()
        inputs = vlm.processor(
            text=text,
            images=[image],
            padding=True,
            return_tensors="pt",
        ).to(vlm.model.device)
        step_time = time.time() - step_start
        print(f"    ✓ Input processing: {step_time:.3f}s")

        # Check GPU memory before generation
        if torch.cuda.is_available():
            print(f"    ✓ Memory before generation: {torch.cuda.memory_allocated() / 1e9:.1f} GB")

        # Step 5: Generation
        step_start = time.time()
        print(f"\n    ⏳ GENERATION STARTING (this is the slow step)...")

        with torch.no_grad():
            output_ids = vlm.model.generate(
                **inputs,
                max_new_tokens=512,
                do_sample=False,
                num_beams=1,
            )

        step_time = time.time() - step_start
        print(f"    ✓ Generation: {step_time:.3f}s ({output_ids.shape[1]} tokens)")

        # Check GPU memory after generation
        if torch.cuda.is_available():
            print(f"    ✓ Memory after generation: {torch.cuda.memory_allocated() / 1e9:.1f} GB")
            print(f"    ✓ Peak memory: {torch.cuda.max_memory_allocated() / 1e9:.1f} GB")

        # Step 6: Decoding
        step_start = time.time()
        generated_ids = [
            output_ids[len(inputs["input_ids"][i]) :]
            for i, output_ids in enumerate(output_ids)
        ]
        response_text = vlm.processor.batch_decode(
            generated_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )[0]
        step_time = time.time() - step_start
        print(f"    ✓ Decoding: {step_time:.3f}s")

        inference_time = time.time() - start_time

        print(f"\n  ✓ Inference completed in {inference_time:.2f}s")
        print(f"  - Response length: {len(response_text)} chars")
        print(f"  - Tokens generated: {output_ids.shape[1]}")
        print(f"  - Throughput: {output_ids.shape[1] / inference_time:.1f} tokens/sec")

        # Show response preview
        print(f"\n  Response preview (first 300 chars):")
        print(f"  {response_text[:300]}")

        # Performance summary
        print(f"\n" + "=" * 80)
        print("PERFORMANCE SUMMARY")
        print("=" * 80)
        print(f"Model load time: {load_time:.2f}s")
        print(f"Inference time: {inference_time:.2f}s")
        print(f"Total time: {load_time + inference_time:.2f}s")
        print(f"Tokens per second: {output_ids.shape[1] / inference_time:.1f}")

        # Analysis
        print(f"\n" + "=" * 80)
        print("ANALYSIS")
        print("=" * 80)

        if inference_time < 5:
            print("✓ EXCELLENT - VLM inference is very fast (GPU-accelerated)")
            print("  Expected end-to-end time per puzzle: 20-30s")
        elif inference_time < 15:
            print("✓ GOOD - VLM inference is reasonable")
            print("  Expected end-to-end time per puzzle: 30-60s")
        elif inference_time < 60:
            print("⚠ SLOW - VLM inference is slow (may not be using GPU efficiently)")
            print("  Expected end-to-end time per puzzle: 60-120s")
        else:
            print("✗ VERY SLOW - VLM inference is very slow (likely CPU-only)")
            print(f"  Expected end-to-end time per puzzle: {inference_time}s or more")

        # GPU check
        if torch.cuda.is_available():
            print(f"\n  GPU is available but may not be fully utilized")
            print(f"  Check GPU during inference with: nvidia-smi")
        else:
            print(f"\n  ⚠ CUDA NOT AVAILABLE - Running on CPU only!")
            print(f"  This is why inference is slow!")
            print(f"  To use GPU:")
            print(f"    1. Check if GPU is available: nvidia-smi")
            print(f"    2. Check CUDA: python -c 'import torch; print(torch.cuda.is_available())'")
            print(f"    3. Reinstall PyTorch with CUDA support if needed")

        # Recommendations
        print(f"\n" + "=" * 80)
        print("RECOMMENDATIONS")
        print("=" * 80)

        if inference_time > 30:
            print("The inference is too slow. Options:")
            print("  1. Check GPU usage: nvidia-smi (should show high utilization)")
            print("  2. If GPU not used, check CUDA installation")
            print("  3. Consider using a smaller model or quantization")
            print("  4. Run inference on a more powerful GPU")

    except Exception as e:
        print(f"✗ Inference failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        vlm.unload_model()
        print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
