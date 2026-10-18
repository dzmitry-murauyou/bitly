"""Запуск сервиса: python run.py

Переменные окружения:
  HOST          — адрес (по умолчанию 0.0.0.0 — доступен в локальной сети)
  PORT          — порт (по умолчанию 8000)
  OPEN_BROWSER  — 1, чтобы автоматически открыть браузер после старта
  DB_PATH, BASE_URL, CODE_LENGTH, API_KEY — см. app/config.py
"""

import os
import socket
import threading
import webbrowser

import uvicorn


def lan_ip() -> str | None:
    """IP компьютера в локальной сети (пакеты никуда не отправляются)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))
            return s.getsockname()[0]
    except OSError:
        return None


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    local_url = f"http://localhost:{port}"

    print()
    print(f"  Сервис:         {local_url}")
    if host == "0.0.0.0" and (ip := lan_ip()):
        print(f"  В локальной сети: http://{ip}:{port}")
    print(f"  API-документация: {local_url}/docs")
    print("  Остановить: Ctrl+C")
    print()

    if os.getenv("OPEN_BROWSER") == "1":
        threading.Timer(1.5, webbrowser.open, args=[local_url]).start()

    uvicorn.run("app.main:app", host=host, port=port, proxy_headers=True)
