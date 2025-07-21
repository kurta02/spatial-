"""
Spatial Constellation Configuration

This package contains configuration management:
- Main configuration classes and environment handling
- LLM model configurations and capabilities
- System settings and deployment options
"""

from .config import Config, LLMConfig, MemoryConfig, get_config

__version__ = "0.5.0"
__all__ = ["Config", "LLMConfig", "MemoryConfig", "get_config"]