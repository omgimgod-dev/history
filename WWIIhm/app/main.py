import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from .database import engine, SessionLocal
from . import models
from .routers import auth, places, forum, tests, admin, home
from .templates_config import env  # ← используем env вместо Jinja2Templates
from passlib.context import CryptContext

# Определяем базовую директорию
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Создаем таблицы в базе данных
models.Base.metadata.create_all(bind=engine)

# Создаем приложение
app = FastAPI()

# Добавляем middleware для сессий
app.add_middleware(SessionMiddleware, secret_key="your-secret-key")

# Подключаем статические файлы
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Подключаем роутеры
app.include_router(auth.router)
app.include_router(places.router)
app.include_router(forum.router)
app.include_router(tests.router)
app.include_router(admin.router)
app.include_router(home.router)

# Middleware для сессии БД
@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    request.state.db = SessionLocal()
    response = await call_next(request)
    request.state.db.close()
    return response

# Создаем папку uploads, если её нет
os.makedirs("app/static/uploads", exist_ok=True)

# Настройка хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Инициализация админа и пользователя при пустой БД
@app.on_event("startup")
def startup():
    db = SessionLocal()
    try:
        if db.query(models.User).count() == 0:
            # Создаем админа — хешируем пароль
            admin = models.User(
                username="admin",
                password=pwd_context.hash("admin123"),  # ← поле password
                is_admin=True
            )
            # Создаем обычного пользователя
            user = models.User(
                username="user",
                password=pwd_context.hash("user123"),  # ← поле password
                is_admin=False
            )
            db.add_all([admin, user])
            db.commit()
            print("✅ Admin and user created successfully")
            print("   Admin login: admin / admin123")
            print("   User login: user / user123")
        else:
            print("✅ Users already exist")
    except Exception as e:
        print(f"❌ Error creating users: {e}")
    finally:
        db.close()
