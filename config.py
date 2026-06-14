"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"
    openrouter_api_key: str = ""
    openrouter_model: str = "anthropic/claude-sonnet-4"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    llm_provider: str = "auto"  # auto | anthropic | openrouter
    redis_url: str = "redis://localhost:6379/0"
    max_retries: int = 3
    use_mock_llm: bool = False
    screenshot_dir: Path = Path("screenshots/current")
    baseline_dir: Path = Path("screenshots/baseline")
    reports_dir: Path = Path("reports")
    scripts_dir: Path = Path("scripts")
    max_repair_before_regenerate: int = 2
    playwright_headless: bool = True
    log_level: str = "INFO"
    langsmith_api_key: str = ""
    langsmith_project: str = "browser-automation-agent"

    @property
    def resolved_llm_provider(self) -> str | None:
        if self.use_mock_llm:
            return None
        if self.llm_provider == "openrouter" and self.openrouter_api_key:
            return "openrouter"
        if self.llm_provider == "anthropic" and self.anthropic_api_key:
            return "anthropic"
        if self.llm_provider == "auto":
            if self.openrouter_api_key:
                return "openrouter"
            if self.anthropic_api_key:
                return "anthropic"
        return None

    @property
    def llm_enabled(self) -> bool:
        return self.resolved_llm_provider is not None

    @property
    def llm_model(self) -> str:
        if self.resolved_llm_provider == "openrouter":
            return self.openrouter_model
        return self.anthropic_model


@lru_cache
def get_settings() -> Settings:
    return Settings()
