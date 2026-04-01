from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Place, User

router = APIRouter(tags=["home"])
templates = Jinja2Templates(directory="app/templates")

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
        main_map_image = places[0].map_image
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
