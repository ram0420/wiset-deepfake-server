from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.models import User
from app.schemas.quiz import (
    QuizCreateResponse, QuizAnswerRequest,
    QuizAnswerResponse, QuizResultResponse
)
from app.services.quiz_service import start_quiz, submit_answer, get_result

router = APIRouter(prefix="/quiz", tags=["quiz"])


@router.get("/start", response_model=QuizCreateResponse)
def start_quiz_api(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return start_quiz(current_user.id, db)


@router.post("/answer", response_model=QuizAnswerResponse)
def answer_quiz(payload: QuizAnswerRequest,
                db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    return submit_answer(
        session_id=payload.session_id,
        question_id=payload.question_id,
        selected_answer=payload.selected_answer,
        user_id=current_user.id,
        db=db
    )


@router.get("/result", response_model=QuizResultResponse)
def quiz_result(session_id: str, db: Session = Depends(get_db)):
    return get_result(session_id, db)
