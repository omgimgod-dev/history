from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from ..models import User, Test, Question, TestAttempt, UserAnswer
from ..database import get_db
from datetime import datetime

router = APIRouter(prefix="/tests", tags=["tests"])
templates = Jinja2Templates(directory="app/templates")

def get_current_user(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if user_id:
        return db.query(User).filter(User.id == user_id).first()
    return None

@router.get("/", response_class=HTMLResponse)
async def tests_list(request: Request, db: Session = Depends(get_db)):
    tests = db.query(Test).all()
    user = get_current_user(request, db)
    return templates.TemplateResponse("tests.html", {
        "request": request,
        "tests": tests,
        "user": user
    })

@router.get("/{test_id}", response_class=HTMLResponse)
async def test_detail(test_id: int, request: Request, db: Session = Depends(get_db)):
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        return RedirectResponse(url="/tests", status_code=404)
    # лучшие результаты: сортировка по баллам (убывание) и дате
    best_attempts = db.query(TestAttempt).filter(
        TestAttempt.test_id == test_id,
        TestAttempt.finished == True
    ).order_by(TestAttempt.score.desc(), TestAttempt.finished_at).limit(10).all()
    user = get_current_user(request, db)
    return templates.TemplateResponse("test_detail.html", {
        "request": request,
        "test": test,
        "best_attempts": best_attempts,
        "user": user
    })

@router.get("/{test_id}/pass", response_class=HTMLResponse)
async def pass_test_start(test_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=302)
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        return RedirectResponse(url="/tests", status_code=404)
    questions = db.query(Question).filter(Question.test_id == test_id).order_by(Question.order).all()
    if not questions:
        return RedirectResponse(url=f"/tests/{test_id}", status_code=302)

    # создаём попытку, если нет незавершённой
    attempt = db.query(TestAttempt).filter(
        TestAttempt.test_id == test_id,
        TestAttempt.user_id == user.id,
        TestAttempt.finished == False
    ).first()
    if not attempt:
        attempt = TestAttempt(
            test_id=test_id,
            user_id=user.id,
            started_at=datetime.utcnow(),
            finished=False,
            score=0
        )
        db.add(attempt)
        db.commit()
        db.refresh(attempt)

    # первый вопрос
    question_index = 0
    question = questions[question_index]
    return templates.TemplateResponse("test_pass.html", {
        "request": request,
        "test": test,
        "questions": questions,
        "current_question": question,
        "question_index": question_index,
        "attempt": attempt,
        "user": user
    })

@router.post("/{test_id}/pass", response_class=HTMLResponse)
async def pass_test_submit(
    test_id: int,
    request: Request,
    question_id: int = Form(...),
    answer: str = Form(...),
    question_index: int = Form(...),
    action: str = Form(...),  # "next", "prev", "finish"
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=302)

    attempt = db.query(TestAttempt).filter(
        TestAttempt.test_id == test_id,
        TestAttempt.user_id == user.id,
        TestAttempt.finished == False
    ).first()
    if not attempt:
        return RedirectResponse(url=f"/tests/{test_id}/pass", status_code=302)

    # сохраняем ответ
    question = db.query(Question).filter(Question.id == question_id).first()
    if question:
        # проверяем, есть ли уже ответ
        existing = db.query(UserAnswer).filter(
            UserAnswer.attempt_id == attempt.id,
            UserAnswer.question_id == question_id
        ).first()
        if existing:
            existing.answer = answer
        else:
            user_answer = UserAnswer(attempt_id=attempt.id, question_id=question_id, answer=answer)
            db.add(user_answer)
        db.commit()

    questions = db.query(Question).filter(Question.test_id == test_id).order_by(Question.order).all()
    total = len(questions)
    next_index = question_index

    if action == "next":
        next_index = min(question_index + 1, total - 1)
    elif action == "prev":
        next_index = max(question_index - 1, 0)
    elif action == "finish":
        # подсчёт результатов
        score = 0
        for q in questions:
            ua = db.query(UserAnswer).filter(
                UserAnswer.attempt_id == attempt.id,
                UserAnswer.question_id == q.id
            ).first()
            if ua and ua.answer == q.correct_answer:
                score += 1
        attempt.score = score
        attempt.finished = True
        attempt.finished_at = datetime.utcnow()
        db.commit()
        return RedirectResponse(url=f"/tests/{test_id}/result/{attempt.id}", status_code=302)

    return RedirectResponse(url=f"/tests/{test_id}/pass?q={next_index}", status_code=302)

# для навигации по точкам (номер вопроса)
@router.get("/{test_id}/pass", response_class=HTMLResponse)
async def pass_test_with_index(
    test_id: int,
    request: Request,
    q: int = 0,
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=302)
    attempt = db.query(TestAttempt).filter(
        TestAttempt.test_id == test_id,
        TestAttempt.user_id == user.id,
        TestAttempt.finished == False
    ).first()
    if not attempt:
        return RedirectResponse(url=f"/tests/{test_id}/pass", status_code=302)

    questions = db.query(Question).filter(Question.test_id == test_id).order_by(Question.order).all()
    total = len(questions)
    if total == 0:
        return RedirectResponse(url=f"/tests/{test_id}", status_code=302)

    q = max(0, min(q, total - 1))
    question = questions[q]
    # предыдущие ответы для подсветки точек
    answers = {ua.question_id: ua.answer for ua in attempt.answers}
    return templates.TemplateResponse("test_pass.html", {
        "request": request,
        "test": db.query(Test).filter(Test.id == test_id).first(),
        "questions": questions,
        "current_question": question,
        "question_index": q,
        "attempt": attempt,
        "answers": answers,
        "user": user
    })

@router.get("/{test_id}/result/{attempt_id}", response_class=HTMLResponse)
async def test_result(test_id: int, attempt_id: int, request: Request, db: Session = Depends(get_db)):
    attempt = db.query(TestAttempt).filter(
        TestAttempt.id == attempt_id,
        TestAttempt.test_id == test_id
    ).first()
    if not attempt or not attempt.finished:
        return RedirectResponse(url=f"/tests/{test_id}", status_code=404)

    test = db.query(Test).filter(Test.id == test_id).first()
    questions = db.query(Question).filter(Question.test_id == test_id).order_by(Question.order).all()
    user_answers = {ua.question_id: ua.answer for ua in attempt.answers}

    results = []
    for q in questions:
        correct = user_answers.get(q.id) == q.correct_answer
        results.append({
            "question": q,
            "user_answer": user_answers.get(q.id, ""),
            "correct": correct
        })

    user = get_current_user(request, db)
    return templates.TemplateResponse("test_result.html", {
        "request": request,
        "test": test,
        "attempt": attempt,
        "results": results,
        "user": user
    })