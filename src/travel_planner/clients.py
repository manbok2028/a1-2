"""Small standard-library clients for OpenAI-compatible and Kakao Local APIs."""

from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .models import Place


class ApiRequestError(RuntimeError):
    """An external API error with a stable category for result logging."""

    def __init__(self, provider: str, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.provider = provider
        self.status_code = status_code

    @property
    def category(self) -> str:
        if self.status_code in {401, 403}:
            return "AUTH_ERROR"
        if self.status_code == 429:
            return "QUOTA_ERROR"
        if self.status_code is not None:
            return "HTTP_ERROR"
        return "NETWORK_ERROR"


class OpenAIClient:
    """Call an OpenAI-compatible chat completions endpoint."""

    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    def complete(self, prompt: str, *, json_mode: bool = False) -> str:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a helpful Korean travel planning assistant."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.4,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        response = _request_json(
            url=f"{self.base_url}/chat/completions",
            method="POST",
            headers={"Authorization": f"Bearer {self.api_key}"},
            payload=payload,
            provider="openai",
        )
        try:
            return str(response["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError) as error:
            raise ApiRequestError("openai", f"Unexpected OpenAI response: {error}") from error


class KakaoLocalClient:
    """Search Korean restaurants with the Kakao Local keyword API."""

    def __init__(self, rest_api_key: str) -> None:
        self.rest_api_key = rest_api_key

    def search_restaurants(self, city: str, limit: int = 5) -> list[Place]:
        query = urlencode({"query": f"{city} 맛집", "size": min(limit, 15)})
        response = _request_json(
            url=f"https://dapi.kakao.com/v2/local/search/keyword.json?{query}",
            method="GET",
            headers={"Authorization": f"KakaoAK {self.rest_api_key}"},
            provider="kakao",
        )
        documents = response.get("documents", [])
        if not isinstance(documents, list):
            raise ApiRequestError("kakao", "Unexpected Kakao response: documents is not a list")
        return [
            Place(
                name=str(item.get("place_name", "")),
                address=str(item.get("road_address_name") or item.get("address_name") or ""),
                category=str(item.get("category_name", "")),
                url=str(item.get("place_url", "")),
                x=_to_float(item.get("x")),
                y=_to_float(item.get("y")),
            )
            for item in documents
            if isinstance(item, dict) and item.get("place_name")
        ]


def _request_json(*, url: str, method: str, headers: dict[str, str], provider: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request_headers = {**headers, "Accept": "application/json"}
    if data is not None:
        request_headers["Content-Type"] = "application/json"
    request = Request(url, data=data, headers=request_headers, method=method)
    try:
        with urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8")
    except HTTPError as error:
        raise ApiRequestError(provider, f"HTTP {error.code}", error.code) from error
    except URLError as error:
        raise ApiRequestError(provider, f"Network error: {error.reason}") from error
    try:
        decoded = json.loads(body)
    except json.JSONDecodeError as error:
        raise ApiRequestError(provider, "Response JSON parsing failed") from error
    if not isinstance(decoded, dict):
        raise ApiRequestError(provider, "Response JSON root is not an object")
    return decoded


def _to_float(value: object) -> float | None:
    try:
        return float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None
