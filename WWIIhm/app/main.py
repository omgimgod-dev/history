import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from .database import engine, SessionLocal
from . import models
from .routers import auth, places, forum, tests, admin, home
from .templates_config import env
from passlib.context import CryptContext

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

# Настройка хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ВРЕМЕННЫЙ ЭНДПОИНТ ДЛЯ СБРОСА ПАРОЛЕЙ
@app.get("/reset-all")
def reset_all_passwords():
    import hashlib
    db = SessionLocal()
    try:
        db.query(models.User).delete()
        
        def simple_hash(password):
            return hashlib.sha256(password.encode()).hexdigest()
        
        admin = models.User(
            username="admin",
            password=simple_hash("admin123"),
            is_admin=True
        )
        user = models.User(
            username="user",
            password=simple_hash("user123"),
            is_admin=False
        )
        
        db.add_all([admin, user])
        db.commit()
        
        return {
            "success": True,
            "message": "All users reset with SHA256!",
            "admin": {"username": "admin", "password": "admin123"},
            "user": {"username": "user", "password": "user123"}
        }
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}
    finally:
        db.close()

# Инициализация админа и пользователя
@app.on_event("startup")
def startup():
    db = SessionLocal()
    try:
        if db.query(models.User).count() == 0:
            print("Creating admin and user...")
            admin = models.User(
                username="admin",
                password=pwd_context.hash("admin123"),
                is_admin=True
            )
            user = models.User(
                username="user",
                password=pwd_context.hash("user123"),
                is_admin=False
            )
            db.add_all([admin, user])
            db.commit()
            print("✅ Admin and user created successfully!")
        else:
            print("✅ Users already exist")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()
