#!/usr/bin/env python
"""Test rule inference module with a few examples."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import init_config, config
from src.utils.logging import setup_logging, get_logger
from src.data.loaders import load_training_examples
from src.models.qwen_model import QwenVLModel
from src.modules.rule_inference import RuleInferenceModule

logger = get_logger(__name__)


def main():
    """Test rule inference."""
    print("=" * 60)
    print("RULE INFERENCE TEST")
    print("=" * 60)

    # Initialize
    init_config()
    setup_logging(config().logging.log_dir, config().logging.log_level)

    # Load a few training examples
    print("\n1. Loading training examples...")
    try:
        dataset = load_training_examples(num_examples=3)
        if len(dataset) == 0:
            print("✗ No training examples found. Please generate dataset first:")
            print("  python scripts/generate_synthetic_sudoku.py --quick")
            return
        print(f"✓ Loaded {len(dataset)} examples")
    except Exception as e:
        print(f"✗ Failed to load examples: {e}")
        return

    # Initialize VLM
    print("\n2. Initializing VLM...")
    vlm = QwenVLModel()
    vlm.load_model()

    # Create rule inference module
    print("\n3. Running rule inference...")
    try:
        rule_module = RuleInferenceModule(vlm)
        examples = list(dataset)
        rules = rule_module.infer_rules(examples, validate=True)

        if rules is None:
            print("✗ Rule inference failed")
            vlm.unload_model()
            return

        print(f"✓ Inferred {len(rules.rules)} rules")
        print("\nInferred Rules:")
        print(rules)

        if rules.metadata:
            print(f"\nConfidence: {rules.metadata.get('confidence', 'N/A')}")
            print(f"Reasoning: {rules.metadata.get('reasoning', 'N/A')[:200]}...")

    except Exception as e:
        print(f"✗ Rule inference failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        vlm.unload_model()

    print("\n" + "=" * 60)
    print("✓ TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
