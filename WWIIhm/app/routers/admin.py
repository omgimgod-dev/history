import os
import shutil
from fastapi import APIRouter, Request, Depends, Form, File, UploadFile, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, Place, ImagePair, Review
from ..templates_config import env
import time
from pathlib import Path

router = APIRouter(prefix="/admin", tags=["admin"])

async def admin_required(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return None  # ← возвращаем None вместо RedirectResponse
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        return None  # ← возвращаем None вместо RedirectResponse
    return user

@router.get("/", response_class=HTMLResponse)
async def admin_panel(request: Request, db: Session = Depends(get_db), admin: User = Depends(admin_required)):
    places = db.query(Place).all()
    main_map_image = "/static/uploads/city_map.jpg"
    if places:
        raw_image = places[0].map_image
        if isinstance(raw_image, tuple):
            main_map_image = raw_image[0] if raw_image else "/static/uploads/city_map.jpg"
        elif isinstance(raw_image, dict):
            main_map_image = raw_image.get('map_image') or raw_image.get('image') or "/static/uploads/city_map.jpg"
        elif raw_image:
            main_map_image = str(raw_image)
    
    template = env.get_template("admin.html")
    content = await template.render_async(
        request=request,
        places=places,
        user=admin,
        main_map_image=main_map_image
    )
    return HTMLResponse(content=content)

@router.get("/edit_place/{place_id}", response_class=HTMLResponse)
async def edit_place(request: Request, place_id: int, db: Session = Depends(get_db), admin: User = Depends(admin_required)):
    place = db.query(Place).filter(Place.id == place_id).first()
    if not place:
        return RedirectResponse(url="/admin", status_code=404)
    
    template = env.get_template("edit_place.html")
    content = await template.render_async(
        request=request,
        place=place,
        user=admin
    )
    return HTMLResponse(content=content)

@router.post("/edit_place/{place_id}")
async def update_place(
    request: Request,
    place_id: int,
    name: str = Form(...),
    description: str = Form(...),
    db: Session = Depends(get_db),
    admin: User = Depends(admin_required)
):
    place = db.query(Place).filter(Place.id == place_id).first()
    if place:
        place.name = name
        place.description = description
        db.commit()
    return RedirectResponse(url=f"/admin/edit_place/{place_id}", status_code=302)

# Добавление новой пары изображений
@router.post("/place/{place_id}/add_pair")
async def add_image_pair(
    request: Request,
    place_id: int,
    modern: UploadFile = File(...),
    past: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: User = Depends(admin_required)
):
    place = db.query(Place).filter(Place.id == place_id).first()
    if not place:
        return JSONResponse(status_code=404, content={"error": "Place not found"})

    # Проверка, что оба файла загружены
    if not modern or not past:
        return JSONResponse(status_code=400, content={"error": "Both modern and past images are required"})

    # Создаём директорию для места, если её нет
    place_dir = f"app/static/uploads/places/{place_id}"
    os.makedirs(place_dir, exist_ok=True)

    # Создаём уникальную подпапку для пары (на основе временной метки)
    timestamp = int(time.time())
    pair_folder = f"pair_{timestamp}"
    pair_path = os.path.join(place_dir, pair_folder)
    os.makedirs(pair_path, exist_ok=True)

    # Сохраняем файлы с фиксированными именами modern и past (сохраняем расширение)
    modern_ext = os.path.splitext(modern.filename)[1]
    past_ext = os.path.splitext(past.filename)[1]
    modern_filename = f"modern{modern_ext}"
    past_filename = f"past{past_ext}"
    modern_path = os.path.join(pair_path, modern_filename)
    past_path = os.path.join(pair_path, past_filename)

    with open(modern_path, "wb") as buffer:
        shutil.copyfileobj(modern.file, buffer)
    with open(past_path, "wb") as buffer:
        shutil.copyfileobj(past.file, buffer)

    # Определяем следующий индекс пары для сортировки
    max_index = db.query(ImagePair).filter(ImagePair.place_id == place_id).count()
    new_pair = ImagePair(
        place_id=place_id,
        modern_path=f"/static/uploads/places/{place_id}/{pair_folder}/{modern_filename}",
        past_path=f"/static/uploads/places/{place_id}/{pair_folder}/{past_filename}",
        pair_index=max_index
    )
    db.add(new_pair)
    db.commit()

    return RedirectResponse(url=f"/admin/edit_place/{place_id}", status_code=302)

# Удаление пары изображений
@router.post("/place/{place_id}/delete_pair/{pair_id}")
async def delete_image_pair(
    request: Request,
    place_id: int,
    pair_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(admin_required)
):
    pair = db.query(ImagePair).filter(ImagePair.id == pair_id, ImagePair.place_id == place_id).first()
    if not pair:
        return RedirectResponse(url=f"/admin/edit_place/{place_id}", status_code=404)

    # Удаляем файлы и папку
    try:
        # Получаем абсолютный путь к папке пары
        modern_full = Path("app" + pair.modern_path)
        pair_dir = os.path.dirname(modern_full)
        if os.path.exists(pair_dir):
            shutil.rmtree(pair_dir)
    except Exception as e:
        # Если не удалось удалить папку, продолжаем (файлы уже могут быть удалены)
        pass

    db.delete(pair)
    db.commit()
    return RedirectResponse(url=f"/admin/edit_place/{place_id}", status_code=302)

@router.post("/upload_map")
async def upload_map(
    request: Request,
    map_image: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: User = Depends(admin_required)
):
    # Удаляем все отзывы, изображения, пары и места
    db.query(Review).delete()
    db.query(ImagePair).delete()
    db.query(Place).delete()
    db.commit()

    upload_dir = "app/static/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, "city_map.jpg")
    if os.path.exists(file_path):
        os.remove(file_path)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(map_image.file, buffer)
    return RedirectResponse(url="/admin", status_code=302)

@router.get("/add_place", response_class=HTMLResponse)
async def add_place_form(request: Request, admin: User = Depends(admin_required)):
    template = env.get_template("add_place.html")
    content = await template.render_async(
        request=request,
        user=admin
    )
    return HTMLResponse(content=content)

@router.post("/add_place_click")
async def add_place_click(
    request: Request,
    name: str = Form(...),
    description: str = Form(...),
    coord_x: float = Form(...),
    coord_y: float = Form(...),
    db: Session = Depends(get_db),
    admin: User = Depends(admin_required)
):
    place = Place(
        name=name,
        description=description,
        coord_x=coord_x,
        coord_y=coord_y,
        creator_id=admin.id
    )
    db.add(place)
    db.commit()
    return RedirectResponse(url="/admin", status_code=302)

@router.post("/delete_place/{place_id}")
async def delete_place(
    request: Request,
    place_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(admin_required)
):
    place = db.query(Place).filter(Place.id == place_id).first()
    if not place:
        return RedirectResponse(url="/admin", status_code=404)
    # Удаляем папку с изображениями места
    place_dir = f"app/static/uploads/places/{place_id}"
    if os.path.exists(place_dir):
        shutil.rmtree(place_dir)
    db.delete(place)
    db.commit()
    return RedirectResponse(url="/admin", status_code=302)
