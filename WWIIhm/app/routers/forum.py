from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from ..models import User, ForumTopic, ForumPost
from ..database import get_db
from datetime import datetime

router = APIRouter(prefix="/forum", tags=["forum"])
templates = Jinja2Templates(directory="app/templates")

def get_current_user(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if user_id:
        return db.query(User).filter(User.id == user_id).first()
    return None

@router.get("/", response_class=HTMLResponse)
async def forum_list(request: Request, db: Session = Depends(get_db)):
    topics = db.query(ForumTopic).order_by(ForumTopic.created_at.desc()).all()
    return templates.TemplateResponse("forum.html", {
        "request": request,
        "topics": topics,
        "user": get_current_user(request, db)
    })

@router.get("/create", response_class=HTMLResponse)
async def create_topic_form(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=302)
    return templates.TemplateResponse("topic_create.html", {
        "request": request,
        "user": user
    })

@router.post("/create", response_class=HTMLResponse)
async def create_topic(
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=302)
    topic = ForumTopic(title=title, content=content, creator_id=user.id, created_at=datetime.utcnow())
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return RedirectResponse(url=f"/forum/topic/{topic.id}", status_code=302)

@router.get("/topic/{topic_id}", response_class=HTMLResponse)
async def view_topic(topic_id: int, request: Request, db: Session = Depends(get_db)):
    topic = db.query(ForumTopic).filter(ForumTopic.id == topic_id).first()
    if not topic:
        return RedirectResponse(url="/forum", status_code=404)
    posts = db.query(ForumPost).filter(ForumPost.topic_id == topic_id).order_by(ForumPost.created_at).all()
    user = get_current_user(request, db)
    return templates.TemplateResponse("topic.html", {
        "request": request,
        "topic": topic,
        "posts": posts,
        "user": user
    })

@router.post("/topic/{topic_id}/post", response_class=HTMLResponse)
async def add_post(
    topic_id: int,
    request: Request,
    content: str = Form(...),
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=302)
    post = ForumPost(content=content, topic_id=topic_id, creator_id=user.id, created_at=datetime.utcnow())
    db.add(post)
    db.commit()
    return RedirectResponse(url=f"/forum/topic/{topic_id}", status_code=302)