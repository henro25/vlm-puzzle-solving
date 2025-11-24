"""Abstract base class for Vision Language Model interfaces."""

from abc import ABC, abstractmethod
from typing import Optional, List, Union
from pathlib import Path
from dataclasses import dataclass
from PIL import Image


@dataclass
class VLMResponse:
    """Response from VLM query."""
    text: str
    model: str
    tokens_used: Optional[int] = None
    raw_response: Optional[dict] = None


class VLMInterface(ABC):
    """Abstract base class for VLM implementations."""

    def __init__(self, model_name: str, device: str = "cuda", **kwargs):
        """
        Initialize VLM interface.

        Args:
            model_name: Name/identifier of the model
            device: Device to run on (cuda/cpu)
            **kwargs: Additional model-specific arguments
        """
        self.model_name = model_name
        self.device = device
        self.kwargs = kwargs

    @abstractmethod
    def query(
        self,
        image: Union[Image.Image, str, Path],
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> VLMResponse:
        """
        Query the VLM with an image and text prompt.

        Args:
            image: PIL Image, image path, or bytes
            prompt: Text prompt to send to VLM
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            VLMResponse with model output
        """
        pass

    @abstractmethod
    def batch_query(
        self,
        images: List[Union[Image.Image, str, Path]],
        prompts: Union[str, List[str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> List[VLMResponse]:
        """
        Query VLM with multiple images (batch).

        Args:
            images: List of images or paths
            prompts: Single prompt (applied to all) or list of prompts
            max_tokens: Maximum tokens per response
            temperature: Sampling temperature

        Returns:
            List of VLMResponse objects
        """
        pass

    @abstractmethod
    def load_model(self) -> None:
        """Load model into memory."""
        pass

    @abstractmethod
    def unload_model(self) -> None:
        """Unload model from memory."""
        pass

    def __enter__(self):
        """Context manager entry."""
        self.load_model()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.unload_model()
