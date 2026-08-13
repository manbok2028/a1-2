"""Environment-variable configuration without third-party dependencies."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


class ConfigurationError(RuntimeError):
    """Raised when a required API key is unavailable."""


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str
    kakao_rest_api_key: str
    gemini_model: str = "gemini-3.5-flash"


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
        if key and (key not in os.environ or not os.environ[key].strip()):
            os.environ[key] = value


def get_settings() -> Settings:
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    kakao_key = os.getenv("KAKAO_REST_API_KEY", "").strip()
    missing = [
        name
        for name, value in (("GEMINI_API_KEY", gemini_key), ("KAKAO_REST_API_KEY", kakao_key))
        if not value
    ]
    if missing:
        joined = ", ".join(missing)
        raise ConfigurationError(
            f"API 키가 설정되지 않았습니다: {joined}\n"
            "Windows PowerShell 예시: $env:GEMINI_API_KEY=\"YOUR_KEY\"\n"
            "$env:KAKAO_REST_API_KEY=\"YOUR_KEY\"\n"
            ".env.example을 복사해 .env 파일에 설정할 수도 있습니다. 실제 키는 Git에 올리지 마세요."
        )
    return Settings(
        gemini_api_key=gemini_key,
        kakao_rest_api_key=kakao_key,
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash").strip() or "gemini-3.5-flash",
    )
