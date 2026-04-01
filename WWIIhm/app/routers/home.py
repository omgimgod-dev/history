import os
from fastapi import APIRouter, Request, Depends

from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Place, User
from ..templates_config import template_engine


router = APIRouter(tags=["home"])


def get_current_user(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if user_id:
        return db.query(User).filter(User.id == user_id).first()
    return None

@router.get("/", response_class=template_engine.TemplateResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    places = db.query(Place).all()
    user = get_current_user(request, db)
    main_map_image = "/static/uploads/city_map.jpg"
    if places:
        raw_image = places[0].map_image
        if isinstance(raw_image, tuple):
            main_map_image = raw_image[0] if raw_image else "/static/uploads/city_map.jpg"
        elif isinstance(raw_image, dict):
            main_map_image = raw_image.get('map_image') or raw_image.get('image') or "/static/uploads/city_map.jpg"
        elif raw_image:
            main_map_image = str(raw_image)
    
    return template_engine.TemplateResponse("index.html", {
        "request": request,
        "places": places,
        "user": user,
        "main_map_image": main_map_image
    })

@router.get("/about", response_class=template_engine.TemplateResponse)
async def about(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    return templates.TemplateResponse("about.html", {"request": request, "user": user})
