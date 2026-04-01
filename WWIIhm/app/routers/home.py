import os
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Place, User

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
router = APIRouter(tags=["home"])
templates = Jinja2Templates(directory=TEMPLATES_DIR)

def get_current_user(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if user_id:
        return db.query(User).filter(User.id == user_id).first()
    return None

@router.get("/", response_class=templates.TemplateResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    places = db.query(Place).all()
    user = get_current_user(request, db)
    
    # Используем изображение карты из первого места или стандартное
    main_map_image = "/static/uploads/city_map.jpg"
    if places:
        # Получаем map_image и преобразуем в строку
        raw_image = places[0].map_image
        # 🔧 ИСПРАВЛЕНИЕ: преобразуем в строку, если это кортеж или словарь
        if isinstance(raw_image, tuple):
            main_map_image = raw_image[0] if raw_image else "/static/uploads/city_map.jpg"
        elif isinstance(raw_image, dict):
            main_map_image = raw_image.get('map_image') or raw_image.get('image') or "/static/uploads/city_map.jpg"
        elif raw_image:
            main_map_image = str(raw_image)
        else:
            main_map_image = "/static/uploads/city_map.jpg"
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "places": places,
        "user": user,
        "main_map_image": main_map_image
    })

@router.get("/about", response_class=templates.TemplateResponse)
async def about(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    return templates.TemplateResponse("about.html", {"request": request, "user": user})
