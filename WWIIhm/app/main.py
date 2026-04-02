import os
import hashlib
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from .database import engine, SessionLocal
from . import models
from .routers import auth, places, forum, tests, admin, home
from .templates_config import env

# Определяем базовую директорию (WWIIhm/app)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Создаем таблицы
models.Base.metadata.create_all(bind=engine)

# Создаем приложение
app = FastAPI()

# Добавляем middleware для сессий
app.add_middleware(SessionMiddleware, secret_key="your-secret-key")

# Подключаем статические файлы (путь к папке static внутри WWIIhm/app)
static_dir = os.path.join(BASE_DIR, "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Создаем папки для загрузок
uploads_dir = os.path.join(static_dir, "uploads")
places_dir = os.path.join(uploads_dir, "places")
avatars_dir = os.path.join(uploads_dir, "avatars")

os.makedirs(uploads_dir, exist_ok=True)
os.makedirs(places_dir, exist_ok=True)
os.makedirs(avatars_dir, exist_ok=True)

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

# --- Функция для SHA256 хеширования ---
def hash_password(password: str) -> str:
    """Возвращает SHA256 хеш пароля."""
    return hashlib.sha256(password.encode()).hexdigest()

# --- Единый эндпоинт для сброса ВСЕХ пользователей и паролей ---
@app.get("/reset-all")
def reset_all_users():
    """Полностью очищает таблицу пользователей и создает админа с user."""
    db = SessionLocal()
    try:
        # 1. Удаляем всех существующих пользователей
        deleted_count = db.query(models.User).delete()
        print(f"Deleted {deleted_count} existing users.")

        # 2. Создаем админа с SHA256 паролем
        admin = models.User(
            username="admin",
            password=hash_password("admin123"),
            is_admin=True
        )
        # 3. Создаем обычного пользователя
        user = models.User(
            username="user",
            password=hash_password("user123"),
            is_admin=False
        )

        db.add_all([admin, user])
        db.commit()

        return {
            "success": True,
            "message": "All users reset! Use SHA256 passwords.",
            "admin": {"username": "admin", "password": "admin123"},
            "user": {"username": "user", "password": "user123"}
        }
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}
    finally:
        db.close()

# --- Упрощенная инициализация БД при старте ---
@app.on_event("startup")
def startup():
    """Проверяет, есть ли пользователи, и если нет — создает админа через SHA256."""
    db = SessionLocal()
    try:
        if db.query(models.User).count() == 0:
            print("Creating initial admin and user with SHA256...")
            admin = models.User(
                username="admin",
                password=hash_password("admin123"),
                is_admin=True
            )
            user = models.User(
                username="user",
                password=hash_password("user123"),
                is_admin=False
            )
            db.add_all([admin, user])
            db.commit()
            print("✅ Admin and user created successfully with SHA256!")
            print("   Admin login: admin / admin123")
            print("   User login: user / user123")
        else:
            print("✅ Users already exist.")
    except Exception as e:
        print(f"❌ Error during startup user check: {e}")
    finally:
        db.close()
