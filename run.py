"""Запуск сервиса: python run.py

Переменные окружения:
  HOST     — адрес (по умолчанию 0.0.0.0 — доступен в локальной сети)
  PORT     — порт (по умолчанию 8000)
  DB_PATH, BASE_URL, CODE_LENGTH, API_KEY — см. app/config.py
"""

import os

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        proxy_headers=True,
    )
