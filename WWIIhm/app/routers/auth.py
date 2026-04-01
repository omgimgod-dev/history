from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models import User
import os
from fastapi import File, UploadFile
import shutil
from ..utils import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="app/templates")


def get_db(request: Request):
    return request.state.db

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not password == user.password:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})
    request.session["user_id"] = user.id
    return RedirectResponse(url="/", status_code=302)

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register")
async def register(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Username already exists"})
    
    user = User(username=username, password=password, is_admin=False)
    db.add(user)
    db.commit()
    request.session["user_id"] = user.id
    return RedirectResponse(url="/", status_code=302)

@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=302)

@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/auth/login")
    user = db.query(User).filter(User.id == user_id).first()
    if user.is_admin: return RedirectResponse(url="/admin/")
    else:return templates.TemplateResponse("profile.html", {"request": request, "user": user})

@router.post("/profile/update")
async def profile_update(request: Request, username: str = Form(...), bio: str = Form(...), db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/auth/login")
    user = db.query(User).filter(User.id == user_id).first()
    user.username = username
    user.bio = bio
    db.commit()
    return RedirectResponse(url="/auth/profile", status_code=302)

@router.post("/profile/change-password")
async def change_password(
    request: Request,
    old_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),  # добавили, если раньше не было
    db: Session = Depends(get_db)
):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/auth/login")
    user = db.query(User).filter(User.id == user_id).first()
    
    # Если пароль не совпадает
    if old_password != user.password:  # в реальном проекте используйте хеширование
        return JSONResponse(content={
            "success": False,
            "error": "Неверный старый пароль",
            "fields": {"old_password": ""}  # подсказка для JS: очистить поле
        })
    
    user.password = new_password
    db.commit()
    return JSONResponse(content={
        "success": True,
        "message": "Пароль успешно изменён",
        
    })

@router.post("/profile/upload-avatar")
async def upload_avatar(request: Request, avatar: UploadFile = File(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=302)
    # сохраняем файл

    base_upload_dir = "app/static/uploads/users"
    user_avatar_dir = os.path.join(base_upload_dir, str(user.id), "avatar")
    os.makedirs(user_avatar_dir, exist_ok=True)
    file_extension = os.path.splitext(avatar.filename)[1]
    file_name = f"avatar_{user.id}{file_extension}"
    file_path = os.path.join(user_avatar_dir, file_name)
    
    if user.avatar and not user.avatar.endswith("default_avatar.png"):
        old_path = os.path.join("app/static", user.avatar.replace("/static/", ""))
        if os.path.exists(old_path):
            os.remove(old_path)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(avatar.file, buffer)
    # обновляем путь в БД
    static_url_path = f"/static/uploads/users/{user.id}/avatar/{file_name}"
    user.avatar = static_url_path
    db.commit()
    return RedirectResponse(url="/auth/profile", status_code=302)

from fastapi import Query

@router.get("/check-username")
async def check_username(username: str = Query(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    return {"available": user is None}