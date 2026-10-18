"""Сервис сокращения ссылок."""

import secrets
import sqlite3
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, status
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from .config import Settings, settings as default_settings
from .db import AliasExistsError, Database
from .schemas import LinkCreate, LinkOut

STATIC_DIR = Path(__file__).parent / "static"


def create_app(settings: Settings = default_settings) -> FastAPI:
    app = FastAPI(
        title="Bitly — сокращатель ссылок",
        description="Простой self-hosted сервис для сокращения ссылок.",
        version="1.0.0",
    )
    db = Database(settings.db_path)
    app.state.db = db
    app.state.settings = settings

    def base_url(request: Request) -> str:
        return settings.base_url or str(request.base_url).rstrip("/")

    def to_out(row: sqlite3.Row, request: Request) -> LinkOut:
        return LinkOut(
            code=row["code"],
            url=row["url"],
            short_url=f"{base_url(request)}/{row['code']}",
            created_at=row["created_at"],
            clicks=row["clicks"],
            last_click_at=row["last_click_at"],
        )

    def require_key(x_api_key: Optional[str] = Header(None)) -> None:
        if settings.api_key and not (
            x_api_key and secrets.compare_digest(x_api_key, settings.api_key)
        ):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Неверный или отсутствующий API-ключ")

    # ---------- Веб-интерфейс ----------

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/health", tags=["service"])
    def health() -> dict:
        return {"status": "ok", "auth_required": bool(settings.api_key)}

    # ---------- API ----------

    @app.post(
        "/api/links",
        response_model=LinkOut,
        status_code=status.HTTP_201_CREATED,
        tags=["links"],
        dependencies=[Depends(require_key)],
    )
    def create_link(payload: LinkCreate, request: Request) -> LinkOut:
        try:
            row = db.create(payload.url, payload.alias, settings.code_length)
        except AliasExistsError:
            raise HTTPException(status.HTTP_409_CONFLICT, "Такой алиас уже занят")
        return to_out(row, request)

    @app.get(
        "/api/links",
        response_model=list[LinkOut],
        tags=["links"],
        dependencies=[Depends(require_key)],
    )
    def list_links(
        request: Request,
        limit: int = Query(100, ge=1, le=1000),
        offset: int = Query(0, ge=0),
    ) -> list[LinkOut]:
        return [to_out(r, request) for r in db.list(limit, offset)]

    @app.get("/api/links/{code}", response_model=LinkOut, tags=["links"])
    def get_link(code: str, request: Request) -> LinkOut:
        row = db.get(code)
        if row is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Ссылка не найдена")
        return to_out(row, request)

    @app.delete(
        "/api/links/{code}",
        status_code=status.HTTP_204_NO_CONTENT,
        tags=["links"],
        dependencies=[Depends(require_key)],
    )
    def delete_link(code: str) -> None:
        if not db.delete(code):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Ссылка не найдена")

    # ---------- Редирект (должен быть последним маршрутом) ----------

    @app.get("/{code}", include_in_schema=False)
    def follow(code: str) -> RedirectResponse:
        url = db.hit(code)
        if url is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Ссылка не найдена")
        # 302, а не 301: браузеры кешируют 301 и счётчик переходов перестаёт расти
        return RedirectResponse(url, status_code=status.HTTP_302_FOUND)

    return app


app = create_app()
