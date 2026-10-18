"""Модели запросов и ответов API."""

import re
from typing import Optional
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator

ALIAS_RE = re.compile(r"^[A-Za-z0-9_-]{3,32}$")
# Домен (в т.ч. IDN/кириллица), IPv4 или IPv6
HOST_RE = re.compile(r"^(?:[\w-]+(?:\.[\w-]+)*\.?|\[?[0-9a-f:.]+\]?)$", re.IGNORECASE)
# Пути, которые заняты самим сервисом и не могут быть алиасами
RESERVED = {"api", "static", "docs", "redoc", "openapi.json", "health", "favicon.ico"}
MAX_URL_LENGTH = 2048


class LinkCreate(BaseModel):
    url: str = Field(..., description="Исходная длинная ссылка", examples=["https://example.com/very/long/path"])
    alias: Optional[str] = Field(None, description="Желаемый короткий код (необязательно)", examples=["my-link"])

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Ссылка не может быть пустой")
        if "://" not in value:
            value = "https://" + value
        if len(value) > MAX_URL_LENGTH:
            raise ValueError(f"Ссылка длиннее {MAX_URL_LENGTH} символов")
        parsed = urlparse(value)
        if parsed.scheme.lower() not in ("http", "https"):
            raise ValueError("Поддерживаются только ссылки http:// и https://")
        try:
            parsed.port  # бросает ValueError на мусоре вроде "javascript:alert(1)"
        except ValueError:
            raise ValueError("Некорректная ссылка") from None
        if not parsed.hostname or not HOST_RE.match(parsed.hostname):
            raise ValueError("Некорректная ссылка")
        return value

    @field_validator("alias")
    @classmethod
    def validate_alias(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        if not value:
            return None
        if not ALIAS_RE.match(value):
            raise ValueError("Алиас: 3–32 символа, только латиница, цифры, «-» и «_»")
        if value.lower() in RESERVED:
            raise ValueError("Этот алиас зарезервирован")
        return value


class LinkOut(BaseModel):
    code: str
    url: str
    short_url: str
    created_at: str
    clicks: int
    last_click_at: Optional[str] = None
