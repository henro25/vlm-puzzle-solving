"""Qwen2-VL Vision Language Model implementation."""

from typing import Optional, List, Union
from pathlib import Path
import torch
from PIL import Image
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
import logging

from .vlm_interface import VLMInterface, VLMResponse
from src.utils.image_processing import load_image, preprocess_image

logger = logging.getLogger(__name__)


class QwenVLModel(VLMInterface):
    """Qwen2-VL Vision Language Model wrapper."""

    def __init__(
        self,
        model_name: str = "Qwen/Qwen2-VL-7B-Instruct",
        device: str = "cuda",
        precision: str = "float16",
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ):
        """
        Initialize Qwen2-VL model.

        Args:
            model_name: Model identifier from HuggingFace
            device: Device to run on (cuda/cpu)
            precision: Model precision (float16/float32)
            max_tokens: Default max tokens for generation
            temperature: Default temperature for sampling
        """
        super().__init__(model_name, device)
        self.precision = precision
        self.default_max_tokens = max_tokens
        self.default_temperature = temperature
        self.model = None
        self.processor = None

    def load_model(self) -> None:
        """Load Qwen2-VL model and processor."""
        logger.info(f"Loading model {self.model_name} on {self.device}")
        print(f"  → Loading checkpoint shards...")

        # Set precision
        dtype = torch.float16 if self.precision == "float16" else torch.float32

        # Load model directly to device (more efficient than CPU->GPU)
        logger.info(f"Loading model directly to {self.device}...")

        # Try with flash_attention_2, fall back if not available
        load_kwargs = {
            "torch_dtype": dtype,
            "device_map": "auto" if self.device == "cuda" else None,
        }

        try:
            # First try with flash_attention_2 (faster but requires flash_attn package)
            self.model = Qwen2VLForConditionalGeneration.from_pretrained(
                self.model_name,
                attn_implementation="flash_attention_2",
                **load_kwargs,
            )
            logger.info("Model loaded with flash_attention_2")

        except (ImportError, ValueError) as e:
            # Flash attention not available, load without it
            logger.warning(f"Flash attention not available ({type(e).__name__}), using standard attention")
            print(f"  → Loading without flash_attention_2 (standard attention)...")

            self.model = Qwen2VLForConditionalGeneration.from_pretrained(
                self.model_name,
                **load_kwargs,
            )
            logger.info("Model loaded with standard attention")

        # If device_map didn't work or CPU requested, move manually
        if self.device == "cuda" and hasattr(self.model, "device") and self.model.device.type != "cuda":
            print(f"  → Moving model to GPU...")
            self.model = self.model.to(self.device)
            logger.info(f"Model moved to {self.device}")

        logger.info(f"Model loaded successfully")

        # Load processor
        print(f"  → Loading processor...")
        self.processor = AutoProcessor.from_pretrained(self.model_name)
        logger.info(f"Processor loaded")

        logger.info(f"✓ Setup complete")

    def unload_model(self) -> None:
        """Unload model from memory."""
        if self.model is not None:
            del self.model
            self.model = None
        if self.processor is not None:
            del self.processor
            self.processor = None
        torch.cuda.empty_cache()
        logger.info("Model unloaded")

    def query(
        self,
        image: Union[Image.Image, str, Path],
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> VLMResponse:
        """
        Query Qwen2-VL with an image and prompt.

        Args:
            image: PIL Image, image path, or bytes
            prompt: Text prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            VLMResponse with model output
        """
        if self.model is None or self.processor is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        # Load image if path provided
        logger.debug("Loading image...")
        if isinstance(image, (str, Path)):
            image = load_image(image)

        max_tokens = max_tokens or self.default_max_tokens
        temperature = temperature or self.default_temperature

        # Prepare inputs using the new API
        logger.debug("Preparing message format...")
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": prompt},
                ],
            }
        ]

        # Process text and image together
        logger.debug("Applying chat template...")
        text = self.processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        # Process inputs (handles image internally)
        logger.debug("Processing inputs (image + text)...")
        inputs = self.processor(
            text=text,
            images=[image],
            padding=True,
            return_tensors="pt",
        ).to(self.device)

        # Generate with optimizations
        logger.debug(f"Generating response (max_tokens={max_tokens})...")
        with torch.no_grad():
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=False,  # Greedy decoding (faster, deterministic)
                num_beams=1,  # No beam search (faster)
            )

        # Decode response
        logger.debug("Decoding response...")
        generated_ids = [
            output_ids[len(inputs["input_ids"][i]) :]
            for i, output_ids in enumerate(output_ids)
        ]
        response_text = self.processor.batch_decode(
            generated_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )[0]

        logger.debug(f"Response generated: {len(response_text)} characters")

        return VLMResponse(
            text=response_text,
            model=self.model_name,
            tokens_used=len(output_ids[0]),
        )

    def batch_query(
        self,
        images: List[Union[Image.Image, str, Path]],
        prompts: Union[str, List[str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> List[VLMResponse]:
        """
        Query Qwen2-VL with multiple images (batch).

        Args:
            images: List of images or paths
            prompts: Single prompt (applied to all) or list of prompts
            max_tokens: Maximum tokens per response
            temperature: Sampling temperature

        Returns:
            List of VLMResponse objects
        """
        if self.model is None or self.processor is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        # Normalize prompts
        if isinstance(prompts, str):
            prompts = [prompts] * len(images)

        # Load images
        loaded_images = []
        for img in images:
            if isinstance(img, (str, Path)):
                img = load_image(img)
            loaded_images.append(img)

        max_tokens = max_tokens or self.default_max_tokens
        temperature = temperature or self.default_temperature

        results = []
        for image, prompt in zip(loaded_images, prompts):
            result = self.query(image, prompt, max_tokens, temperature)
            results.append(result)

        return results
