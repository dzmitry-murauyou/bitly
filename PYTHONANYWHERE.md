# Деплой на PythonAnywhere

FastAPI — ASGI-фреймворк, а мастер PythonAnywhere умеет только WSGI (Django, Flask, …).
Поэтому в проекте есть `wsgi.py`: он оборачивает приложение адаптером [a2wsgi](https://pypi.org/project/a2wsgi/).
В мастере выбирайте **Manual configuration**.

Подходит бесплатный аккаунт (Beginner). Сайт будет доступен по адресу `https://<логин>.pythonanywhere.com`.

> Ниже везде `USERNAME` — ваш логин на PythonAnywhere.

## 1. Загрузить код и установить зависимости

Откройте **Consoles → Bash** и выполните:

```bash
git clone https://github.com/dzmitry-murauyou/bitly.git
cd bitly
mkvirtualenv --python=python3.12 bitly
pip install -r requirements.txt
```

> Можно взять любую версию Python от 3.10 и выше, которая есть на PythonAnywhere.
> Главное, чтобы в шаге 2 вы выбрали **ту же** версию.
> Если команда `mkvirtualenv` не найдена, используйте:
> `python3.12 -m venv ~/.virtualenvs/bitly && source ~/.virtualenvs/bitly/bin/activate`

## 2. Создать веб-приложение

1. Вкладка **Web**, кнопка **Add a new web app**, затем **Next**.
2. **Select a Python Web framework**: выберите **Manual configuration**.
3. Выберите **Python 3.12** (ту же версию, что в шаге 1), затем **Next**.

## 3. Настроить приложение (вкладка Web)

**Virtualenv:**
```
/home/USERNAME/.virtualenvs/bitly
```

**Code:**
- Source code: `/home/USERNAME/bitly`
- Working directory: `/home/USERNAME/bitly`

**WSGI configuration file.** Нажмите на ссылку `/var/www/USERNAME_pythonanywhere_com_wsgi.py`,
**удалите всё содержимое** и вставьте содержимое файла
[`deploy/pythonanywhere_wsgi.py`](deploy/pythonanywhere_wsgi.py). В нём:

```python
USERNAME = "USERNAME"  # <-- замените на свой логин
# os.environ["API_KEY"] = "..."   # <-- рекомендуется раскомментировать
```

Нажмите **Save**.

**Static files** (необязательно, но статика будет отдаваться быстрее):

| URL        | Directory                           |
|------------|-------------------------------------|
| `/static/` | `/home/USERNAME/bitly/app/static`   |

**Security:** включите **Force HTTPS**.

## 4. Запустить

Нажмите зелёную кнопку **Reload USERNAME.pythonanywhere.com** и откройте сайт.

## Защита API-ключом

Сайт публичный: без ключа кто угодно сможет создавать ссылки на вашем домене.
Раскомментируйте в WSGI-файле строку с `API_KEY`, придумайте длинный ключ и нажмите **Reload**.
В веб-интерфейсе появится поле для ключа. Переходы по коротким ссылкам при этом работают для всех.

Сгенерировать ключ можно в Bash-консоли:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(24))"
```

## Обновление

```bash
cd ~/bitly
git pull
workon bitly
pip install -r requirements.txt
```
Затем нажмите **Reload** на вкладке Web. База (`~/bitly/data/links.db`) при обновлении сохраняется.

## Если что-то не работает

- **«Something went wrong :-(»**: на вкладке Web откройте **Error log** (внизу, в разделе Log files). Последние строки покажут причину.
- **`ModuleNotFoundError: No module named 'fastapi'` / `'a2wsgi'`**: не указан Virtualenv, версия Python в нём не совпадает с версией веб-приложения, или не выполнен `pip install -r requirements.txt`.
- **`ModuleNotFoundError: No module named 'wsgi'`**: в WSGI-файле не заменён `USERNAME`, или проект склонирован не в `/home/USERNAME/bitly`.
- **Короткие ссылки начинаются с `http://` или с чужого адреса**: проверьте `BASE_URL` в WSGI-файле.
- **На бесплатном аккаунте сайт выключается через 3 месяца**: раз в 3 месяца заходите на вкладку Web и нажимайте **Run until 3 months from today**.
