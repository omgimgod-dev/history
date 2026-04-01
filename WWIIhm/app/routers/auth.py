from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..templates_config import env  # ← импортируем окружение
from passlib.context import CryptContext
from fastapi import Form

router = APIRouter(tags=["auth"])
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
    
    if not user or not pwd_context.verify(password, user.hashed_password):
        template = env.get_template("login.html")
        content = await template.render_async(
            request=request,
            error="Неверное имя пользователя или пароль"
        )
        return HTMLResponse(content=content)
    
    # Успешный вход
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
    # Проверяем, существует ли пользователь
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
    
    # Создаем нового пользователя
    hashed_password = pwd_context.hash(password)
    new_user = User(
        username=username,
        email=email,
        hashed_password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Автоматически входим после регистрации
    request.session["user_id"] = new_user.id
    return RedirectResponse(url="/", status_code=303)

@router.get("/logout")
async def logout(request: Request):
    """Выход из системы"""
    request.session.clear()
    return RedirectResponse(url="/")
