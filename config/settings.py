import enum
import os
from typing import Optional

from pydantic import ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict

from config.config_parser import docker_args
from utils.sqlalchemy import async_db_url

args = docker_args


class LogLevel(enum.Enum):
    """Possible log levels."""
    NOTSET = "NOTSET"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    FATAL = "FATAL"


class Settings(BaseSettings):
    """Application settings for Trend Analysis."""

    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="allow"  # Allow dynamic fields like connection_manager
    )

    # Application
    env: str = args.env
    port: int = args.port
    host: str = args.host
    debug: bool = args.debug
    workers_count: int = 1
    mode: str = args.mode

    # Database
    postgres_url: str = args.postgres_url
    db_url: str = async_db_url(args.postgres_url)
    db_echo: bool = args.debug

    # Redis
    redis_url: str = args.redis_url

    # AI Models
    openai_api_key: str = args.openai_api_key

    # Logging
    log_level: str = LogLevel.INFO.value

    # Streaming
    stream_token: str = "data"

    # Base directory
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Connection managers (set at runtime)
    connection_manager: Optional[any] = None


loaded_config = Settings()
