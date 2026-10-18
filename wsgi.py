"""WSGI-точка входа для хостингов без поддержки ASGI (PythonAnywhere и т.п.).

FastAPI — ASGI-фреймворк, поэтому оборачиваем его адаптером a2wsgi.
Хостинг должен импортировать отсюда объект `application`.
"""

import os
import sys

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from a2wsgi import ASGIMiddleware  # noqa: E402

from app.main import app as asgi_app  # noqa: E402

application = ASGIMiddleware(asgi_app)
