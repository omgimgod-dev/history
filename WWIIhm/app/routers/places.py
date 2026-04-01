from fastapi import APIRouter, Request, Form, Depends, HTTPException, UploadFile, File
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models import Place, Review, User
import os
import shutil

router = APIRouter(prefix="/places", tags=["places"])
templates = Jinja2Templates(directory="app/templates")

def get_db(request: Request):
    return request.state.db

@router.get("/", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db)):
    places = db.query(Place).all()
    # главное фото города (можно взять из первого места или отдельной настройки)
    main_image = "/static/uploads/city_map.jpg"  # заглушка
    return templates.TemplateResponse("index.html", {"request": request, "places": places, "main_image": main_image})

@router.get("/place/{place_id}", response_class=HTMLResponse)
async def place_detail(request: Request, place_id: int, db: Session = Depends(get_db)):
    place = db.query(Place).filter(Place.id == place_id).first()
    if not place:
        raise HTTPException(status_code=404)
    reviews = db.query(Review).filter(Review.place_id == place_id).order_by(Review.created_at.desc()).limit(5).all()
    return templates.TemplateResponse("place.html", {"request": request, "place": place, "reviews": reviews})

@router.post("/place/{place_id}/review")
async def add_review(request: Request, place_id: int, text: str = Form(...), db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/auth/login", status_code=302)
    review = Review(place_id=place_id, user_id=user_id, text=text)
    db.add(review)
    db.commit()
    return RedirectResponse(url=f"/places/place/{place_id}", status_code=302)

# Админские функции добавления/редактирования места будут в admin.py+