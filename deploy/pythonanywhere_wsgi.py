# ============================================================================
#  Шаблон WSGI-файла для PythonAnywhere.
#
#  Скопируйте ВСЁ содержимое этого файла в WSGI-файл веб-приложения
#  (вкладка Web → ссылка "WSGI configuration file", обычно
#  /var/www/<USERNAME>_pythonanywhere_com_wsgi.py), удалив всё, что там было.
#  Затем замените USERNAME на ваш логин и нажмите Reload.
# ============================================================================

import os
import sys

USERNAME = "USERNAME"  # <-- ваш логин на PythonAnywhere

PROJECT_DIR = f"/home/{USERNAME}/bitly"
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

# Настройки задаются ДО импорта приложения
os.environ["BASE_URL"] = f"https://{USERNAME}.pythonanywhere.com"
os.environ["DB_PATH"] = f"{PROJECT_DIR}/data/links.db"

# Рекомендуется: сайт публичный, без ключа кто угодно сможет создавать ссылки.
# Придумайте длинный случайный ключ и раскомментируйте строку:
# os.environ["API_KEY"] = "замените-на-свой-секретный-ключ"

from wsgi import application  # noqa: E402,F401
