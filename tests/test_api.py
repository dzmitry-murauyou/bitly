import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app(Settings(db_path=str(tmp_path / "test.db"), base_url="", code_length=6, api_key=""))
    return TestClient(app)


@pytest.fixture
def secured(tmp_path):
    app = create_app(Settings(db_path=str(tmp_path / "test.db"), base_url="http://sho.rt", code_length=6, api_key="secret"))
    return TestClient(app)


def test_index(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "сокращатель ссылок" in r.text


def test_create_and_redirect(client):
    r = client.post("/api/links", json={"url": "https://example.com/a?b=1"})
    assert r.status_code == 201
    data = r.json()
    assert len(data["code"]) == 6
    assert data["short_url"] == f"http://testserver/{data['code']}"

    r = client.get(f"/{data['code']}", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"] == "https://example.com/a?b=1"

    stats = client.get(f"/api/links/{data['code']}").json()
    assert stats["clicks"] == 1
    assert stats["last_click_at"]


def test_scheme_added(client):
    r = client.post("/api/links", json={"url": "example.com"})
    assert r.json()["url"] == "https://example.com"


@pytest.mark.parametrize("url", ["https://localhost:8080/x", "http://192.168.1.1", "https://пример.рф/путь", "example.com:3000"])
def test_valid_urls(client, url):
    assert client.post("/api/links", json={"url": url}).status_code == 201


@pytest.mark.parametrize("url", ["", "javascript:alert(1)", "data:text/html,hi", "ftp://x.com", "https://", "http://a b.com"])
def test_invalid_url(client, url):
    assert client.post("/api/links", json={"url": url}).status_code == 422


def test_custom_alias(client):
    r = client.post("/api/links", json={"url": "https://example.com", "alias": "my-link"})
    assert r.status_code == 201
    assert r.json()["code"] == "my-link"
    r = client.post("/api/links", json={"url": "https://other.com", "alias": "my-link"})
    assert r.status_code == 409


@pytest.mark.parametrize("alias", ["ab", "api", "with space", "кириллица", "x" * 33])
def test_bad_alias(client, alias):
    assert client.post("/api/links", json={"url": "https://e.com", "alias": alias}).status_code == 422


def test_list_and_delete(client):
    codes = [client.post("/api/links", json={"url": f"https://e.com/{i}"}).json()["code"] for i in range(3)]
    listed = [l["code"] for l in client.get("/api/links").json()]
    assert listed == codes[::-1]
    assert client.delete(f"/api/links/{codes[0]}").status_code == 204
    assert client.delete(f"/api/links/{codes[0]}").status_code == 404
    assert client.get(f"/{codes[0]}", follow_redirects=False).status_code == 404


def test_not_found(client):
    assert client.get("/nope", follow_redirects=False).status_code == 404


def test_api_key(secured):
    assert secured.post("/api/links", json={"url": "https://e.com"}).status_code == 401
    assert secured.get("/api/links").status_code == 401
    r = secured.post("/api/links", json={"url": "https://e.com"}, headers={"X-API-Key": "secret"})
    assert r.status_code == 201
    assert r.json()["short_url"].startswith("http://sho.rt/")
    # Переход по ссылке доступен без ключа
    assert secured.get(f"/{r.json()['code']}", follow_redirects=False).status_code == 302
    assert secured.get("/health").json()["auth_required"] is True


def test_stats(client):
    assert client.get("/api/stats").json() == {"links": 0, "clicks": 0}
    code = client.post("/api/links", json={"url": "https://e.com"}).json()["code"]
    client.get(f"/{code}", follow_redirects=False)
    client.get(f"/{code}", follow_redirects=False)
    client.post("/api/links", json={"url": "https://e.org"})
    assert client.get("/api/stats").json() == {"links": 2, "clicks": 2}


def test_wsgi_entrypoint(tmp_path, monkeypatch):
    """Проверяем, что приложение работает через WSGI (как на PythonAnywhere)."""
    import importlib
    import sys
    from wsgiref.util import setup_testing_defaults

    monkeypatch.setenv("DB_PATH", str(tmp_path / "wsgi.db"))
    for mod in ("wsgi", "app.main", "app.config"):
        sys.modules.pop(mod, None)
    wsgi = importlib.import_module("wsgi")

    def call(method, path, body=b""):
        import io
        environ = {}
        setup_testing_defaults(environ)
        environ.update({
            "REQUEST_METHOD": method, "PATH_INFO": path,
            "CONTENT_TYPE": "application/json", "CONTENT_LENGTH": str(len(body)),
            "wsgi.input": io.BytesIO(body),
        })
        captured = {}

        def start_response(status, headers, exc_info=None):
            captured["status"], captured["headers"] = status, dict(headers)

        data = b"".join(wsgi.application(environ, start_response))
        return captured["status"], captured["headers"], data

    status, _, data = call("POST", "/api/links", b'{"url": "https://example.com", "alias": "wsgi-test"}')
    assert status.startswith("201"), data
    status, headers, _ = call("GET", "/wsgi-test")
    assert status.startswith("302")
    assert headers["location"] == "https://example.com"
    status, _, data = call("GET", "/")
    assert status.startswith("200") and "bitly".encode() in data

    for mod in ("wsgi", "app.main", "app.config"):
        sys.modules.pop(mod, None)
