import os
from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Place, Review, User
from ..templates_config import env

router = APIRouter(prefix="/places", tags=["places"])

def get_current_user(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if user_id:
        return db.query(User).filter(User.id == user_id).first()
    return None

def place_to_dict(place: Place) -> dict:
    """Преобразует объект Place в словарь для шаблона"""
    return {
        "id": place.id,
        "name": place.name,
        "description": place.description,
        "coord_x": place.coord_x,
        "coord_y": place.coord_y,
        "map_image": place.map_image,
        "creator_id": place.creator_id,
        "created_at": place.created_at,
        "image_pairs": place.image_pairs  # это отношение, его нужно будет обработать отдельно
    }

@router.get("/place/{place_id}", response_class=HTMLResponse)
async def place_detail(request: Request, place_id: int, db: Session = Depends(get_db)):
    place = db.query(Place).filter(Place.id == place_id).first()
    if not place:
        raise HTTPException(status_code=404, detail="Место не найдено")
    
    # Явно загружаем image_pairs с сортировкой
    reviews = db.query(Review).filter(Review.place_id == place_id).all()
    user = get_current_user(request, db)
    
    # Принудительно загружаем image_pairs, чтобы они были доступны в шаблоне
    # SQLAlchemy лениво загружает отношения, но в шаблоне они должны быть доступны
    # Если не работают, можно сделать:
    image_pairs = db.query(ImagePair).filter(ImagePair.place_id == place_id).order_by(ImagePair.pair_index).all()
    
    template = env.get_template("place.html")
    content = await template.render_async(
        request=request,
        place=place,
        image_pairs=image_pairs,  # ← передаём отдельно
        reviews=reviews,
        user=user
    )
    return HTMLResponse(content=content)

@router.post("/place/{place_id}/review", response_class=HTMLResponse)
async def add_review(
    request: Request,
    place_id: int,
    rating: int = Form(...),
    comment: str = Form(...),
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)
    
    place = db.query(Place).filter(Place.id == place_id).first()
    if not place:
        raise HTTPException(status_code=404, detail="Место не найдено")
    
    new_review = Review(
        rating=rating,
        comment=comment,
        place_id=place_id,
        user_id=user.id
    )
    db.add(new_review)
    db.commit()
    
    return RedirectResponse(url=f"/places/place/{place_id}", status_code=303)
