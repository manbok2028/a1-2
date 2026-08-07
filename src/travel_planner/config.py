"""Environment-variable configuration without third-party dependencies."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


class ConfigurationError(RuntimeError):
    """Raised when a required API key is unavailable."""


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    kakao_rest_api_key: str
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4.1-mini"


def load_dotenv(path: Path) -> None:
    """Load simple KEY=VALUE entries without overwriting real environment values."""
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", maxsplit=1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def get_settings() -> Settings:
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    kakao_key = os.getenv("KAKAO_REST_API_KEY", "").strip()
    missing = [name for name, value in (("OPENAI_API_KEY", openai_key), ("KAKAO_REST_API_KEY", kakao_key)) if not value]
    if missing:
        joined = ", ".join(missing)
        raise ConfigurationError(
            f"API 키가 설정되지 않았습니다: {joined}\n"
            "Windows PowerShell 예시: $env:OPENAI_API_KEY=\"YOUR_KEY\"\n"
            "$env:KAKAO_REST_API_KEY=\"YOUR_KEY\"\n"
            ".env.example을 복사해 .env 파일에 설정할 수도 있습니다. 실제 키는 절대 Git에 올리지 마세요."
        )
    return Settings(
        openai_api_key=openai_key,
        kakao_rest_api_key=kakao_key,
        openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
    )
