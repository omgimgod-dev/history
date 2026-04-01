import os

from fastapi.templating import Jinja2Templates
from jinja2 import FileSystemLoader, Environment

# Абсолютный путь к папке templates
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")

# Создаем окружение Jinja2 с отключенным кэшем
jinja2_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    auto_reload=True,  # Перезагружать шаблоны при изменении
    cache_size=0       # ОТКЛЮЧАЕМ КЭШ
)

# Создаем Jinja2Templates с нашим окружением
templates = Jinja2Templates(env=jinja2_env)
