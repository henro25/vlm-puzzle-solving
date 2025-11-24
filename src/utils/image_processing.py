"""Image processing utilities for Sudoku and puzzle images."""

from pathlib import Path
from typing import Union, Tuple
import numpy as np
from PIL import Image
import logging

logger = logging.getLogger(__name__)


def load_image(image_path: Union[str, Path]) -> Image.Image:
    """
    Load an image from file.

    Args:
        image_path: Path to image file

    Returns:
        PIL Image object
    """
    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    image = Image.open(image_path)
    if image.mode != "RGB":
        image = image.convert("RGB")
    return image


def resize_image(image: Image.Image, target_size: Tuple[int, int]) -> Image.Image:
    """
    Resize image to target size while maintaining aspect ratio with padding.

    Args:
        image: PIL Image object
        target_size: Target size (height, width)

    Returns:
        Resized PIL Image
    """
    target_h, target_w = target_size
    orig_w, orig_h = image.size

    # Calculate scale to fit within target while maintaining aspect ratio
    scale = min(target_w / orig_w, target_h / orig_h)
    new_w = int(orig_w * scale)
    new_h = int(orig_h * scale)

    # Resize image
    image = image.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # Create new image with padding
    padded = Image.new("RGB", (target_w, target_h), color=(255, 255, 255))
    pad_x = (target_w - new_w) // 2
    pad_y = (target_h - new_h) // 2
    padded.paste(image, (pad_x, pad_y))

    return padded


def image_to_array(image: Image.Image) -> np.ndarray:
    """
    Convert PIL Image to numpy array normalized to [0, 1].

    Args:
        image: PIL Image object

    Returns:
        Numpy array (H, W, 3) with values in [0, 1]
    """
    array = np.array(image).astype(np.float32) / 255.0
    return array


def array_to_image(array: np.ndarray) -> Image.Image:
    """
    Convert numpy array to PIL Image.

    Args:
        array: Numpy array (H, W, 3) with values in [0, 1] or [0, 255]

    Returns:
        PIL Image object
    """
    if array.max() <= 1.0:
        array = (array * 255).astype(np.uint8)
    else:
        array = array.astype(np.uint8)

    return Image.fromarray(array)


def preprocess_image(image_path: Union[str, Path], target_size: Tuple[int, int] = (448, 448)) -> np.ndarray:
    """
    Load and preprocess image for VLM input.

    Args:
        image_path: Path to image
        target_size: Target size (height, width)

    Returns:
        Preprocessed image as numpy array
    """
    image = load_image(image_path)
    image = resize_image(image, target_size)
    array = image_to_array(image)
    return array


def save_image(image: Image.Image, output_path: Union[str, Path], quality: int = 95) -> None:
    """
    Save image to file.

    Args:
        image: PIL Image object
        output_path: Output file path
        quality: JPEG quality (1-100)
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.suffix.lower() in [".jpg", ".jpeg"]:
        image.save(output_path, quality=quality)
    else:
        image.save(output_path)


def enhance_contrast(image: Image.Image, factor: float = 1.5) -> Image.Image:
    """
    Enhance image contrast to improve digit visibility.

    Args:
        image: PIL Image object
        factor: Contrast enhancement factor

    Returns:
        Enhanced PIL Image
    """
    from PIL import ImageEnhance
    enhancer = ImageEnhance.Contrast(image)
    return enhancer.enhance(factor)
