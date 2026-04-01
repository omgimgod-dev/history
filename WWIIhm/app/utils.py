from fastapi import Depends, Request
from sqlalchemy.orm import Session
from .database import get_db
from .models import User

def get_current_user(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if user_id:
        return db.query(User).filter(User.id == user_id).first()
    return None
