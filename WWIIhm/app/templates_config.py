import os
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Абсолютный путь к папке templates
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")

# Создаем окружение Jinja2 вручную
env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(['html', 'xml']),
    auto_reload=True,
    cache_size=0,  # Полностью отключаем кэш
    enable_async=True  # Поддержка async
)
