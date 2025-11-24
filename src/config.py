"""Configuration management for Visual Constraint Discovery system."""

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class VLMConfig(BaseModel):
    """Vision Language Model configuration."""
    model_name: str = Field(default="Qwen/Qwen2-VL-7B-Instruct", description="VLM model identifier")
    device: str = Field(default="cuda", description="Device to run model on (cuda/cpu)")
    max_tokens: int = Field(default=1024, description="Max tokens for generation")
    temperature: float = Field(default=0.7, description="Temperature for sampling")
    precision: str = Field(default="float16", description="Model precision (float16/float32)")


class DataConfig(BaseModel):
    """Data pipeline configuration."""
    data_dir: Path = Field(default=Path("./data"), description="Base data directory")
    raw_dir: Path = Field(default=Path("./data/raw"), description="Raw data directory")
    processed_dir: Path = Field(default=Path("./data/processed"), description="Processed data directory")
    ground_truth_dir: Path = Field(default=Path("./data/ground_truth"), description="Ground truth directory")

    # Sudoku specific
    num_train_examples: int = Field(default=100, description="Number of solved examples for training")
    num_test_puzzles: int = Field(default=200, description="Number of test puzzles")

    def __init__(self, **data):
        super().__init__(**data)
        # Create directories if they don't exist
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.ground_truth_dir.mkdir(parents=True, exist_ok=True)


class ImageConfig(BaseModel):
    """Image processing configuration."""
    image_size: tuple = Field(default=(448, 448), description="Target image size for VLM")
    max_size: tuple = Field(default=(672, 672), description="Maximum image size")
    image_format: str = Field(default="RGB", description="Image format")
    quality: int = Field(default=95, description="JPEG quality if saving")


class CSPConfig(BaseModel):
    """CSP solver configuration."""
    solver_type: str = Field(default="python-constraint", description="CSP solver library")
    timeout: int = Field(default=60, description="Solver timeout in seconds")
    use_constraint_propagation: bool = Field(default=True, description="Use constraint propagation")
    heuristic: str = Field(default="MRV", description="Variable selection heuristic")


class EvaluationConfig(BaseModel):
    """Evaluation configuration."""
    results_dir: Path = Field(default=Path("./results"), description="Results directory")
    save_visualizations: bool = Field(default=True, description="Save visualization plots")
    save_metrics: bool = Field(default=True, description="Save metrics to JSON")
    verbose: bool = Field(default=True, description="Verbose output")

    def __init__(self, **data):
        super().__init__(**data)
        (self.results_dir / "figures").mkdir(parents=True, exist_ok=True)
        (self.results_dir / "metrics").mkdir(parents=True, exist_ok=True)


class LoggingConfig(BaseModel):
    """Logging configuration."""
    log_dir: Path = Field(default=Path("./results/logs"), description="Log directory")
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>", description="Log format")

    def __init__(self, **data):
        super().__init__(**data)
        self.log_dir.mkdir(parents=True, exist_ok=True)


class Config(BaseModel):
    """Main configuration object."""
    # Sub-configurations
    vlm: VLMConfig = Field(default_factory=VLMConfig)
    data: DataConfig = Field(default_factory=DataConfig)
    image: ImageConfig = Field(default_factory=ImageConfig)
    csp: CSPConfig = Field(default_factory=CSPConfig)
    evaluation: EvaluationConfig = Field(default_factory=EvaluationConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    # Experiment settings
    seed: int = Field(default=42, description="Random seed")
    verbose: bool = Field(default=True, description="Verbose output")

    class Config:
        arbitrary_types_allowed = True


def get_config() -> Config:
    """Get configuration from environment and defaults."""
    return Config(
        vlm=VLMConfig(
            model_name=os.getenv("VLM_MODEL", "Qwen/Qwen2-VL-7B-Instruct"),
            device=os.getenv("DEVICE", "cuda"),
        ),
        data=DataConfig(
            data_dir=Path(os.getenv("DATA_DIR", "./data")),
        ),
        evaluation=EvaluationConfig(
            results_dir=Path(os.getenv("RESULTS_DIR", "./results")),
        ),
        logging=LoggingConfig(
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_dir=Path(os.getenv("LOG_DIR", "./results/logs")),
        ),
        seed=int(os.getenv("SEED", "42")),
    )


# Global config instance
_config: Optional[Config] = None


def init_config(config: Optional[Config] = None) -> Config:
    """Initialize global config."""
    global _config
    _config = config or get_config()
    return _config


def config() -> Config:
    """Get global config instance."""
    global _config
    if _config is None:
        _config = get_config()
    return _config
