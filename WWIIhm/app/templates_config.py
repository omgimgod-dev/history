import os
from fastapi.templating import Jinja2Templates

# Абсолютный путь к папке templates
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")

# Создаем объект шаблонов с отключенным кэшированием
template_engine = Jinja2Templates(directory=TEMPLATES_DIR)
template_engine.env.cache_size = 0  # Отключаем кэш
