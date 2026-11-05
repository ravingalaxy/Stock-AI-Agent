"""Configuration management using Pydantic Settings."""

import os
from pathlib import Path
from typing import Optional
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent.parent / "config" / ".env"
if env_path.exists():
    load_dotenv(env_path, override=True)
else:
    # Try default locations
    load_dotenv(override=True)


class SystemConfig(BaseSettings):
    project_name: str = "AI Stock Market Research & Ranking Agent"
    version: str = "1.0.0"
    log_level: str = "INFO"
    log_file: str = "data/logs/stock_agent.log"
    cache_dir: str = "data/raw"
    db_path: str = "sqlite:///data/stock_research.db"
    vector_db_path: str = "data/chroma_db"
    market_data_provider: str = "yfinance"


class ScreeningDefaults(BaseSettings):
    min_market_cap_cr: float = 500.0
    min_avg_daily_volume: int = 50000
    min_avg_daily_turnover_cr: float = 0.5
    exclude_penny_stocks: bool = True
    min_share_price: float = 10.0
    allowed_exchanges: list = ["NSE", "BSE"]


class DataFetchingConfig(BaseSettings):
    price_history_period: str = "2y"
    request_timeout: int = 15
    max_retries: int = 3
    backoff_factor: int = 2
    news_fetch_limit: int = 15
    news_lookback_days: int = 30


class ScoringWeights(BaseSettings):
    quality: float = 0.30
    growth: float = 0.20
    valuation: float = 0.15
    momentum: float = 0.15
    catalyst: float = 0.10
    risk_penalty: float = 0.10


class LLMConfig(BaseSettings):
    provider: str = "freellmapi"  # 'openai', 'ollama', or 'freellmapi'
    model_name: str = "gpt-4o-mini"  # Model to use (freellmapi supports: gpt-4o-mini, gpt-4o, claude-3.5-sonnet, etc.)
    temperature: float = 0.2
    max_tokens: int = 2048
    embedding_model: str = "text-embedding-3-small"
    
    # OpenAI
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_api_base: str = Field(default="https://api.openai.com/v1", alias="OPENAI_API_BASE")
    
    # Freellmapi (Unified API)
    freellmapi_api_key: Optional[str] = Field(default=None, alias="FREELLM_API_KEY")
    freellmapi_api_base: str = Field(default="https://api.freellmapi.com/v1", alias="FREELLM_API_BASE")
    
    # Ollama
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    ollama_model_name: str = Field(default="llama3.2", alias="OLLAMA_MODEL_NAME")
    
    model_config = SettingsConfigDict(protected_namespaces=('settings_',))


class BacktestDefaults(BaseSettings):
    initial_capital: float = 1000000.0
    top_n_stocks: int = 10
    rebalance_frequency: str = "M"
    transaction_cost_pct: float = 0.001
    benchmark_symbol: str = "^NSEI"


class ComplianceConfig(BaseSettings):
    disclaimer: str = (
        "DISCLAIMER: This report and ranking system is an AI-assisted personal research "
        "and educational decision-support tool only. It does NOT constitute personalized "
        "investment advice, financial advisory services, or stock recommendations. "
        "Stock market investments are subject to market risks. Read all related documents "
        "carefully before investing. Past performance is not an indicator or guarantee of "
        "future returns. No assured or guaranteed returns are claimed or implied."
    )


class AppConfig(BaseSettings):
    system: SystemConfig = SystemConfig()
    screening_defaults: ScreeningDefaults = ScreeningDefaults()
    data_fetching: DataFetchingConfig = DataFetchingConfig()
    scoring_weights: ScoringWeights = ScoringWeights()
    llm: LLMConfig = LLMConfig()
    backtest_defaults: BacktestDefaults = BacktestDefaults()
    compliance: ComplianceConfig = ComplianceConfig()
    
    model_config = SettingsConfigDict(
        env_nested_delimiter="__", 
        extra="ignore",
        protected_namespaces=('settings_',)
    )


@lru_cache()
def get_config() -> AppConfig:
    """Get cached application configuration."""
    return AppConfig()


# For direct access
config = get_config()