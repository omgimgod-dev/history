from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..templates_config import env
from passlib.context import CryptContext
import hashlib

router = APIRouter(prefix="/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Страница входа"""
    template = env.get_template("login.html")
    content = await template.render_async(request=request)
    return HTMLResponse(content=content)

@router.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Обработка входа"""
    user = db.query(User).filter(User.username == username).first()
    
    if not user:
        template = env.get_template("login.html")
        content = await template.render_async(
            request=request,
            error="Неверное имя пользователя или пароль"
        )
        return HTMLResponse(content=content)
    
    # Проверяем тип пароля в базе
    if user.password.startswith('$2b$'):
        # Это bcrypt хеш
        if not pwd_context.verify(password, user.password):
            template = env.get_template("login.html")
            content = await template.render_async(
                request=request,
                error="Неверное имя пользователя или пароль"
            )
            return HTMLResponse(content=content)
    else:
        # Это SHA256 хеш (временное решение)
        hashed = hashlib.sha256(password.encode()).hexdigest()
        if user.password != hashed:
            template = env.get_template("login.html")
            content = await template.render_async(
                request=request,
                error="Неверное имя пользователя или пароль"
            )
            return HTMLResponse(content=content)
    
    request.session["user_id"] = user.id
    return RedirectResponse(url="/", status_code=303)

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Страница регистрации"""
    template = env.get_template("register.html")
    content = await template.render_async(request=request)
    return HTMLResponse(content=content)

@router.post("/register", response_class=HTMLResponse)
async def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Обработка регистрации"""
    existing_user = db.query(User).filter(
        (User.username == username) | (User.email == email)
    ).first()
    
    if existing_user:
        template = env.get_template("register.html")
        content = await template.render_async(
            request=request,
            error="Пользователь с таким именем или email уже существует"
        )
        return HTMLResponse(content=content)
    
    # Хешируем пароль и сохраняем в поле password
    hashed_password = pwd_context.hash(password)
    new_user = User(
        username=username,
        email=email,
        password=hashed_password,  # ← сохраняем в поле password
        is_admin=False
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    request.session["user_id"] = new_user.id
    return RedirectResponse(url="/", status_code=303)

@router.get("/logout")
async def logout(request: Request):
    """Выход из системы"""
    request.session.clear()
    return RedirectResponse(url="/")
