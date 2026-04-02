from fastapi import APIRouter, Request, Depends, HTTPException, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..templates_config import env
import hashlib
import os
import shutil

router = APIRouter(prefix="/auth", tags=["auth"])

def hash_password(password: str) -> str:
    """Возвращает SHA256 хеш пароля."""
    return hashlib.sha256(password.encode()).hexdigest()

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
    """Обработка входа (только SHA256)."""
    user = db.query(User).filter(User.username == username).first()

    if not user:
        template = env.get_template("login.html")
        content = await template.render_async(
            request=request,
            error="Неверное имя пользователя или пароль"
        )
        return HTMLResponse(content=content)

    # Проверяем пароль через SHA256
    hashed_input_password = hash_password(password)
    if user.password != hashed_input_password:
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
    """Обработка регистрации (сохраняем SHA256 хеш)."""
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

    # Сохраняем хеш пароля
    hashed_password = hash_password(password)
    new_user = User(
        username=username,
        email=email,
        password=hashed_password,
        is_admin=False
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    request.session["user_id"] = new_user.id
    return RedirectResponse(url="/", status_code=303)

@router.get("/profile", response_class=HTMLResponse)
async def profile(request: Request, db: Session = Depends(get_db)):
    """Страница профиля пользователя"""
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/auth/login", status_code=303)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)
    
    template = env.get_template("profile.html")
    content = await template.render_async(
        request=request,
        user=user
    )
    return HTMLResponse(content=content)

@router.post("/profile/update")
async def update_profile(
    request: Request,
    username: str = Form(...),
    bio: str = Form(None),
    db: Session = Depends(get_db)
):
    """Обновление профиля"""
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/auth/login", status_code=303)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)
    
    # Проверяем, не занято ли имя пользователя
    existing_user = db.query(User).filter(
        User.username == username,
        User.id != user_id
    ).first()
    
    if existing_user:
        template = env.get_template("profile.html")
        content = await template.render_async(
            request=request,
            user=user,
            error="Это имя пользователя уже занято"
        )
        return HTMLResponse(content=content)
    
    user.username = username
    user.bio = bio or ""
    db.commit()
    
    return RedirectResponse(url="/auth/profile", status_code=303)

@router.post("/profile/upload-avatar")
async def upload_avatar(
    request: Request,
    avatar: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Загрузка аватара"""
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/auth/login", status_code=303)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)
    
    # Создаем директорию для аватаров
    upload_dir = "app/static/uploads/avatars"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Сохраняем файл
    file_ext = os.path.splitext(avatar.filename)[1]
    filename = f"user_{user_id}{file_ext}"
    file_path = os.path.join(upload_dir, filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(avatar.file, buffer)
    
    # Обновляем путь к аватару в базе
    user.avatar = f"/static/uploads/avatars/{filename}"
    db.commit()
    
    return RedirectResponse(url="/auth/profile", status_code=303)

@router.post("/profile/change-password")
async def change_password(
    request: Request,
    old_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Изменение пароля (JSON ответ для AJAX) - только SHA256"""
    user_id = request.session.get("user_id")
    if not user_id:
        return JSONResponse(
            status_code=401,
            content={"success": False, "error": "Необходимо войти в систему"}
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": "Пользователь не найден"}
        )
    
    # Проверяем старый пароль через SHA256 (упрощенно)
    old_hashed = hash_password(old_password)
    if user.password != old_hashed:
        return JSONResponse(
            content={"success": False, "error": "Неверный старый пароль"}
        )
    
    # Проверяем совпадение нового пароля
    if new_password != confirm_password:
        return JSONResponse(
            content={"success": False, "error": "Новый пароль и подтверждение не совпадают"}
        )
    
    # Проверяем длину нового пароля
    if len(new_password) < 6:
        return JSONResponse(
            content={"success": False, "error": "Новый пароль должен содержать минимум 6 символов"}
        )
    
    # Сохраняем новый пароль (SHA256)
    new_hashed = hash_password(new_password)
    user.password = new_hashed
    db.commit()
    
    return JSONResponse(
        content={"success": True, "message": "Пароль успешно изменен"}
    )

@router.get("/logout")
async def logout(request: Request):
    """Выход из системы"""
    request.session.clear()
    return RedirectResponse(url="/")
