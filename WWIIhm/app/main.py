import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from .database import engine, SessionLocal
from . import models
from .routers import auth, places, forum, tests, admin, home
from .templates_config import env
from passlib.context import CryptContext

# Определяем базовую директорию
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Создаем таблицы
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

# ========== ВРЕМЕННЫЙ ЭНДПОИНТ ДЛЯ ФИКСА ПАРОЛЕЙ ==========
@app.get("/fix-passwords")
def fix_passwords():
    """Временный эндпоинт для хеширования паролей"""
    db = SessionLocal()
    try:
        users = db.query(models.User).all()
        fixed_count = 0
        results = []
        
        for user in users:
            try:
                # Если пароль не начинается с $2b$ (признак bcrypt хеша)
                if not user.password.startswith('$2b$'):
                    old_password = user.password
                    # Обрезаем пароль до 72 байт (ограничение bcrypt)
                    # Преобразуем в bytes, обрезаем, потом обратно в строку
                    password_bytes = old_password.encode('utf-8')[:72]
                    truncated_password = password_bytes.decode('utf-8', errors='ignore')
                    
                    print(f"Fixing password for user: {user.username}")
                    print(f"  Original length: {len(old_password)} chars")
                    print(f"  Truncated to: {len(truncated_password)} chars")
                    
                    user.password = pwd_context.hash(truncated_password)
                    fixed_count += 1
                    results.append({
                        "id": user.id,
                        "username": user.username,
                        "status": "fixed",
                        "old_length": len(old_password),
                        "new_length": len(truncated_password)
                    })
                else:
                    results.append({
                        "id": user.id,
                        "username": user.username,
                        "status": "already_hashed"
                    })
            except Exception as e:
                results.append({
                    "id": user.id,
                    "username": user.username,
                    "status": "error",
                    "error": str(e)
                })
        
        db.commit()
        
        return {
            "success": True,
            "fixed_count": fixed_count,
            "total_users": len(users),
            "results": results,
            "message": f"Fixed {fixed_count} passwords"
        }
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}
    finally:
        db.close()
# =========================================================
@app.get("/force-reset-passwords")
def force_reset_passwords():
    """Принудительный сброс паролей"""
    db = SessionLocal()
    try:
        # Получаем всех пользователей
        users = db.query(models.User).all()
        results = []
        
        for user in users:
            # Устанавливаем новый пароль
            new_password = "admin123" if user.is_admin else "user123"
            user.password = pwd_context.hash(new_password)
            results.append({
                "id": user.id,
                "username": user.username,
                "is_admin": user.is_admin,
                "new_password": new_password
            })
        
        db.commit()
        
        return {
            "success": True,
            "message": "Passwords reset successfully!",
            "users": results
        }
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}
    finally:
        db.close()
# Инициализация админа и пользователя при пустой БД
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
            print("   Admin login: admin / admin123")
            print("   User login: user / user123")
        else:
            print("✅ Users already exist")
    except Exception as e:
        print(f"❌ Error creating users: {e}")
    finally:
        db.close()
