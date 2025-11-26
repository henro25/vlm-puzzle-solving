#!/usr/bin/env python
"""Test VLM inference in isolation to measure speed."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import init_config, config
from src.utils.logging import setup_logging, get_logger
from src.data.loaders import load_training_examples
from src.models.qwen_model import QwenVLModel
from src.prompts.rule_inference_prompts import get_rule_inference_prompt

logger = get_logger(__name__)


def main():
    """Test VLM inference speed."""
    print("=" * 70)
    print("VLM INFERENCE SPEED TEST")
    print("=" * 70)

    # Initialize
    print("\n[1] Initializing config...")
    init_config()
    setup_logging(config().logging.log_dir, config().logging.log_level)

    # Load data
    print("[2] Loading training examples...")
    try:
        examples = load_training_examples(num_examples=1)
        if not examples:
            print("✗ No examples loaded")
            return
        print(f"  ✓ Loaded {len(examples)} example")
    except Exception as e:
        print(f"✗ Failed to load data: {e}")
        return

    # Initialize VLM
    print("\n[3] Loading VLM model...")
    vlm = QwenVLModel()

    start = time.time()
    vlm.load_model()
    load_time = time.time() - start
    print(f"  ✓ Model loaded in {load_time:.1f}s")

    # Test inference
    print("\n[4] Testing VLM inference...")
    example = examples[0]

    prompt = get_rule_inference_prompt(num_examples=1)
    print(f"  Prompt length: {len(prompt)} chars")
    print(f"  Image: {example.image_path}")

    try:
        print(f"\n  Starting inference...")
        start_inference = time.time()

        response = vlm.query(
            image=example.image_path,
            prompt=prompt,
            max_tokens=2048,
        )

        inference_time = time.time() - start_inference

        print(f"\n  ✓ Inference completed in {inference_time:.2f}s")
        print(f"  Response length: {len(response.text)} chars")
        print(f"  Tokens generated: {response.tokens_used}")
        print(f"  Throughput: {response.tokens_used / inference_time:.1f} tokens/sec")

        # Show response
        print(f"\n  Response preview (first 500 chars):")
        print(f"  {response.text[:500]}")

        # Performance metrics
        print(f"\n" + "=" * 70)
        print("PERFORMANCE METRICS")
        print("=" * 70)
        print(f"Model load time: {load_time:.2f}s")
        print(f"Inference time: {inference_time:.2f}s")
        print(f"Total time: {load_time + inference_time:.2f}s")
        print(f"Tokens per second: {response.tokens_used / inference_time:.1f}")

        # Interpretation
        print(f"\n" + "=" * 70)
        print("INTERPRETATION")
        print("=" * 70)
        if inference_time < 5:
            print("✓ FAST - Inference is quick (GPU enabled)")
        elif inference_time < 15:
            print("⚠ MEDIUM - Reasonable inference speed")
        elif inference_time < 30:
            print("⚠ SLOW - Inference is slow (check GPU usage)")
        else:
            print("✗ VERY SLOW - Likely CPU-only or GPU issues")

        print(f"\nWith 3 training examples, expect ~{inference_time * 1:.1f}s for rule inference")
        print(f"Full end-to-end should take ~{load_time + inference_time * 1 + 5:.0f}-{load_time + inference_time * 1 + 15:.0f}s")

    except Exception as e:
        print(f"✗ Inference failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        vlm.unload_model()
        print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
