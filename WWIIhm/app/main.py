from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from .database import engine, SessionLocal
from . import models
from .routers import auth, places, forum, tests, admin, home
import os
from .templates_config import TEMPLATES_DIR
# Определяем базовую директорию
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="your-secret-key")
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

app.include_router(auth.router)
app.include_router(places.router)
app.include_router(forum.router)
app.include_router(tests.router)
app.include_router(admin.router)
app.include_router(home.router)

# middleware для сессии БД
@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    request.state.db = SessionLocal()
    response = await call_next(request)
    request.state.db.close()
    return response

# создание папки uploads
os.makedirs("app/static/uploads", exist_ok=True)

# инициализация админа и пользователя при пустой БД
from .database import SessionLocal
from .models import User
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@app.on_event("startup")
def startup():
    db = SessionLocal()
    if db.query(User).count() == 0:
        admin = User(username="admin", password ="admin123", is_admin=True)
        user = User(username="user", password="user123", is_admin=False)
        db.add_all([admin, user])
        db.commit()
    db.close()
