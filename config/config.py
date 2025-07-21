#!/usr/bin/env python3
"""
Spatial Constellation System Configuration
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Main configuration class"""
    
    # Base paths
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    LOGS_DIR = DATA_DIR / "logs"
    WORKSPACE_DIR = DATA_DIR / "workspace"
    
    # Database configuration
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB = os.getenv("POSTGRES_DB", "spatial_constellation")
    POSTGRES_USER = os.getenv("POSTGRES_USER", "spatial_ai")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
    
    # Database URL for SQLAlchemy
    DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    
    # LLM API configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    
    # Local LLM configuration
    LOCAL_LLM_HOST = os.getenv("LOCAL_LLM_HOST", "localhost")
    LOCAL_LLM_PORT = int(os.getenv("LOCAL_LLM_PORT", "11434"))
    LOCAL_LLM_MODEL = os.getenv("LOCAL_LLM_MODEL", "llama3")
    
    # Flask configuration
    FLASK_HOST = os.getenv("FLASK_HOST", "localhost")
    FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    
    # System configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    DEFAULT_PERMISSION_MODE = os.getenv("DEFAULT_PERMISSION_MODE", "readonly")
    ENABLE_FILE_OPERATIONS = os.getenv("ENABLE_FILE_OPERATIONS", "true").lower() == "true"
    SANDBOX_MODE = os.getenv("SANDBOX_MODE", "true").lower() == "true"
    
    # Logging paths
    LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", str(LOGS_DIR / "system.log"))
    CONVERSATION_LOG_PATH = os.getenv("CONVERSATION_LOG_PATH", str(DATA_DIR / "conversations"))
    
    @classmethod
    def ensure_directories(cls):
        """Ensure all required directories exist"""
        for directory in [cls.DATA_DIR, cls.LOGS_DIR, cls.WORKSPACE_DIR]:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def validate_config(cls):
        """Validate required configuration"""
        required_vars = [
            ("OPENAI_API_KEY", cls.OPENAI_API_KEY),
            ("ANTHROPIC_API_KEY", cls.ANTHROPIC_API_KEY),
            ("POSTGRES_PASSWORD", cls.POSTGRES_PASSWORD)
        ]
        
        missing = [name for name, value in required_vars if not value]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

class LLMConfig:
    """LLM-specific configuration"""
    
    CHATGPT_CONFIG = {
        "model": "gpt-4o",
        "temperature": 0.7,
        "max_tokens": 4000,
        "timeout": 30
    }
    
    CLAUDE_CONFIG = {
        "model": "claude-3-5-sonnet-20241022",
        "temperature": 0.7,
        "max_tokens": 4000,
        "timeout": 30
    }
    
    LOCAL_CONFIG = {
        "model": Config.LOCAL_LLM_MODEL,
        "temperature": 0.7,
        "max_tokens": 4000,
        "timeout": 60
    }

class MemoryConfig:
    """Memory system configuration"""
    
    # Vector dimensions for embeddings
    VECTOR_DIMENSION = 384
    
    # Memory retention settings
    MAX_MEMORY_ENTRIES = 10000
    MEMORY_CLEANUP_INTERVAL = 24 * 60 * 60  # 24 hours in seconds
    
    # Context window settings
    MAX_CONTEXT_LENGTH = 8000
    CONTEXT_OVERLAP = 500

# Development vs Production settings
class DevelopmentConfig(Config):
    """Development-specific configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production-specific configuration"""
    DEBUG = False
    TESTING = False
    LOG_LEVEL = "WARNING"

class TestingConfig(Config):
    """Testing-specific configuration"""
    DEBUG = True
    TESTING = True
    DATABASE_URL = "sqlite:///:memory:"

# Configuration selector
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(env=None):
    """Get configuration based on environment"""
    if env is None:
        env = os.getenv('FLASK_ENV', 'default')
    return config_map.get(env, DevelopmentConfig)