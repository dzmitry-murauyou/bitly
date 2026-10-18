# bitly — свой сокращатель ссылок

Сервис для сокращения ссылок на Python, который можно поднять у себя на компьютере.

- **FastAPI** + **SQLite**: ставить отдельную базу данных не нужно, всё хранится в одном файле `data/links.db`
- Современный веб-интерфейс с тёмной (по умолчанию) и светлой темой: сокращение, свой адрес, копирование, поиск, удаление
- Счётчик переходов и время последнего перехода
- REST API со Swagger-документацией на `/docs`
- Можно закрыть API-ключом, чтобы ссылки создавали только вы
- Запуск одной командой: скриптом или через Docker
- Готов к деплою на **PythonAnywhere**: см. [PYTHONANYWHERE.md](PYTHONANYWHERE.md)

## Быстрый старт

Нужен **Python 3.10+**.

### Windows
Дважды кликните по `start.bat`. Он сам найдёт Python, создаст виртуальное окружение,
поставит зависимости, запустит сервер и откроет браузер. В окне будет показан адрес для доступа из локальной сети.

Если Python не установлен, скачайте его с [python.org](https://www.python.org/downloads/)
и при установке отметьте **Add python.exe to PATH**.

### Linux / macOS
```bash
./start.sh
```

### Вручную
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

### PythonAnywhere
Пошаговая инструкция: [PYTHONANYWHERE.md](PYTHONANYWHERE.md).

### Docker
```bash
docker compose up -d --build
```
База хранится в папке `./data` и не пропадает при пересоздании контейнера.

---

После запуска откройте **http://localhost:8000**.

С других устройств в вашей сети (телефона, другого ПК) сервис доступен по адресу `http://<IP-вашего-ПК>:8000`.
IP можно узнать командой `ipconfig` (Windows) или `ip a` (Linux). Если не открывается, разрешите порт 8000 в брандмауэре.

## Настройки

Все настройки задаются переменными окружения:

| Переменная    | По умолчанию     | Описание |
|---------------|------------------|----------|
| `HOST`        | `0.0.0.0`        | Адрес, на котором слушает сервер. Укажите `127.0.0.1`, чтобы сервис был доступен только с этого ПК |
| `PORT`        | `8000`           | Порт |
| `OPEN_BROWSER`| *(пусто)*        | `1`: открыть браузер после запуска (`start.bat` включает это сам) |
| `DB_PATH`     | `data/links.db`  | Путь к файлу базы (по умолчанию внутри папки проекта) |
| `BASE_URL`    | *(пусто)*        | Публичный адрес для коротких ссылок, например `http://192.168.1.10:8000` или `https://s.example.com`. Если пусто, адрес берётся из запроса |
| `CODE_LENGTH` | `6`              | Длина случайного кода (62⁶ ≈ 56 млрд вариантов) |
| `API_KEY`     | *(пусто)*        | Если задан, то создавать, удалять и смотреть список ссылок можно только с заголовком `X-API-Key`. Переходы по коротким ссылкам остаются открытыми для всех |

Пример:
```bash
# Linux/macOS
PORT=8080 API_KEY=my-secret python run.py
# Windows PowerShell
$env:PORT=8080; $env:API_KEY="my-secret"; python run.py
```

Если задан `API_KEY`, в веб-интерфейсе появится поле для ключа (он запоминается в браузере).

## API

| Метод    | Путь                  | Описание |
|----------|-----------------------|----------|
| `POST`   | `/api/links`          | Создать ссылку: `{"url": "...", "alias": "необязательно"}` |
| `GET`    | `/api/links`          | Список ссылок (`?limit=100&offset=0`) |
| `GET`    | `/api/links/{code}`   | Информация и статистика по ссылке |
| `GET`    | `/api/stats`          | Всего ссылок и переходов |
| `DELETE` | `/api/links/{code}`   | Удалить ссылку |
| `GET`    | `/{code}`             | Редирект (302) на исходный адрес |
| `GET`    | `/health`             | Проверка работоспособности |

Пример:
```bash
curl -X POST http://localhost:8000/api/links \
     -H "Content-Type: application/json" \
     -d '{"url": "https://github.com/dzmitry-murauyou/bitly", "alias": "repo"}'
```
```json
{
  "code": "repo",
  "url": "https://github.com/dzmitry-murauyou/bitly",
  "short_url": "http://localhost:8000/repo",
  "created_at": "2026-10-18T12:00:00+00:00",
  "clicks": 0,
  "last_click_at": null
}
```

Интерактивная документация: http://localhost:8000/docs

### Правила
- Принимаются только ссылки `http://` и `https://`. Если схема не указана, подставляется `https://`
- Алиас: 3–32 символа, латиница, цифры, `-` и `_`. Служебные имена (`api`, `docs`, `static`, …) заняты
- Используется редирект 302, а не 301: иначе браузеры кешируют переход и счётчик перестаёт расти

## Тесты

```bash
pip install -r requirements-dev.txt
pytest
```

## Структура

```
app/
  main.py       — маршруты FastAPI
  db.py         — работа с SQLite
  schemas.py    — валидация входных данных
  config.py     — настройки из переменных окружения
  static/       — веб-интерфейс (HTML/CSS/JS)
tests/          — тесты
run.py          — точка входа (uvicorn)
wsgi.py         — WSGI-точка входа (PythonAnywhere)
deploy/         — шаблон WSGI-файла для PythonAnywhere
start.bat/.sh   — запуск в один клик
Dockerfile, docker-compose.yml
```
