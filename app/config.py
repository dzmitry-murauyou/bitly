"""Настройки сервиса. Всё задаётся через переменные окружения."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    # Путь к файлу SQLite-базы
    db_path: str = os.getenv("DB_PATH", "data/links.db")
    # Публичный адрес сервиса для формирования коротких ссылок,
    # например http://192.168.1.10:8000. Если пусто — берётся из запроса.
    base_url: str = os.getenv("BASE_URL", "").rstrip("/")
    # Длина автоматически генерируемого кода
    code_length: int = int(os.getenv("CODE_LENGTH", "6"))
    # Если задан — создание/удаление/просмотр списка ссылок требует
    # заголовок "X-API-Key: <значение>". Переходы по ссылкам открыты всем.
    api_key: str = os.getenv("API_KEY", "")


settings = Settings()
