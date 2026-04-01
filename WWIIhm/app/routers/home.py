import os
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Place, User
from ..templates_config import TEMPLATES_DIR

templates = Jinja2Templates(directory=TEMPLATES_DIR)
router = APIRouter(tags=["home"])


def get_current_user(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if user_id:
        return db.query(User).filter(User.id == user_id).first()
    return None

@router.get("/", response_class=templates.TemplateResponse)
@router.get("/", response_class=templates.TemplateResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    print("=== DEBUG: home endpoint called ===")
    
    try:
        places = db.query(Place).all()
        print(f"DEBUG: places type = {type(places)}, count = {len(places)}")
        print(f"DEBUG: first place type = {type(places[0]) if places else 'None'}")
        
        user = get_current_user(request, db)
        print(f"DEBUG: user = {user}")
        
        main_map_image = "/static/uploads/city_map.jpg"
        if places:
            raw_image = places[0].map_image
            print(f"DEBUG: raw_image type = {type(raw_image)}")
            print(f"DEBUG: raw_image value = {raw_image}")
            
            # Безопасное преобразование
            try:
                if isinstance(raw_image, tuple):
                    main_map_image = raw_image[0] if raw_image else "/static/uploads/city_map.jpg"
                elif isinstance(raw_image, dict):
                    main_map_image = raw_image.get('map_image') or raw_image.get('image') or "/static/uploads/city_map.jpg"
                elif raw_image is not None:
                    main_map_image = str(raw_image)
            except Exception as e:
                print(f"DEBUG: error converting image: {e}")
                main_map_image = "/static/uploads/city_map.jpg"
        
        print(f"DEBUG: final main_map_image = {main_map_image}")
        print(f"DEBUG: preparing template response")
        
        response = templates.TemplateResponse("index.html", {
            "request": request,
            "places": places,
            "user": user,
            "main_map_image": main_map_image
        })
        
        print("DEBUG: template response created successfully")
        return response
        
    except Exception as e:
        print(f"DEBUG: CAUGHT EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        raise

@router.get("/about", response_class=templates.TemplateResponse)
async def about(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    return templates.TemplateResponse("about.html", {"request": request, "user": user})
