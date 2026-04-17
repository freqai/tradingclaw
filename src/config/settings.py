"""
Configuration module for AI Trading Agent System
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """System configuration settings"""

    # System
    SYSTEM_NAME: str = "ai-trading-agent"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # TDengine
    TDENGINE_HOST: str = "localhost"
    TDENGINE_PORT: int = 6041
    TDENGINE_USER: str = "root"
    TDENGINE_PASSWORD: str = "taosdata"
    TDENGINE_DATABASE: str = "trading_data"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    # Exchange
    EXCHANGE_NAME: str = "binance"
    API_KEY: Optional[str] = None
    API_SECRET: Optional[str] = None
    TESTNET: bool = True

    # AI Models
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"

    # Trading
    DEFAULT_SYMBOL: str = "BTC/USDT"
    DEFAULT_TIMEFRAME: str = "1h"
    MAX_POSITION_SIZE: float = 1000.0
    STOP_LOSS_PERCENT: float = 2.0
    TAKE_PROFIT_PERCENT: float = 5.0

    # Risk Management
    MAX_DAILY_LOSS: float = 500.0
    MAX_CONCURRENT_TRADES: int = 5
    RISK_PER_TRADE: float = 0.02

    # Human-in-the-Loop
    REQUIRE_HUMAN_APPROVAL: bool = True
    APPROVAL_TIMEOUT_SECONDS: int = 300

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
