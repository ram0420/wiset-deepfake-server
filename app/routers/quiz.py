# /api/v1/quiz 라우터 (random, answer)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import uuid4
from app.dependencies import get_db, get_current_user
from app.models import QuizSession, QuizQuestion, QuizAnswer, UserProfile
from app.schemas.quiz import (
    QuizCreateResponse, QuizQuestionResponse, QuizAnswerRequest, QuizAnswerResponse, QuizResultResponse
)

router = APIRouter(prefix="/quiz", tags=["quiz"])


@router.post("", response_model=QuizCreateResponse, status_code=201)
def create_quiz(db: Session = Depends(get_db), user=Depends(get_current_user)):
    quiz_id = str(uuid4())
    session = QuizSession(id=quiz_id, user_id=user.id)
    db.add(session)

    # 예시용 랜덤 문제 10개 생성 (실제 구현 시 문제은행 활용)
    for i in range(10):
        question = QuizQuestion(
            quiz_id=quiz_id,
            question_number=i + 1,
            question=f"문제 {i + 1}번 내용",
            options=["A", "B", "C", "D"],
            correct_answer="A",
            explanation="정답은 A입니다."
        )
        db.add(question)

    db.commit()
    return {"quizId": quiz_id, "message": "랜덤 퀴즈 세트가 생성되었습니다. 이제 퀴즈를 시작하세요."}


@router.get("/{quizId}/current", response_model=QuizQuestionResponse)
def get_current_question(quizId: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    answered_numbers = db.query(QuizAnswer.question_number).filter_by(quiz_id=quizId, user_id=user.id).all()
    answered_set = {q[0] for q in answered_numbers}
    question = db.query(QuizQuestion).filter(
        QuizQuestion.quiz_id == quizId,
        ~QuizQuestion.question_number.in_(answered_set)
    ).order_by(QuizQuestion.question_number).first()

    if not question:
        raise HTTPException(status_code=404, detail="더 이상 남은 문제가 없습니다.")

    return {
        "quizId": quizId,
        "questionNumber": question.question_number,
        "question": question.question,
        "options": question.options
    }


@router.post("/{quizId}/answer", response_model=QuizAnswerResponse)
def submit_answer(quizId: str, data: QuizAnswerRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    question = db.query(QuizQuestion).filter_by(quiz_id=quizId, question_number=data.questionNumber).first()
    if not question:
        raise HTTPException(status_code=404, detail="해당 문제를 찾을 수 없습니다.")

    correct = question.correct_answer == data.answer
    answer = QuizAnswer(
        quiz_id=quizId,
        user_id=user.id,
        question_number=data.questionNumber,
        selected_answer=data.answer,
        correct=correct
    )
    db.add(answer)

    # 점수 계산 방식 예시: 정답당 10점
    score = db.query(QuizAnswer).filter_by(quiz_id=quizId, user_id=user.id, correct=True).count() * 10
    db.commit()

    return {
        "correct": correct,
        "explanation": question.explanation,
        "score": score,
        "message": "정답 여부 및 해설 제공"
    }


@router.get("/{quizId}/result", response_model=QuizResultResponse)
def get_quiz_result(quizId: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    profile = db.query(UserProfile).filter_by(user_id=user.id).first()
    username = profile.nickname if profile else user.email

    total = db.query(QuizQuestion).filter_by(quiz_id=quizId).count()
    correct = db.query(QuizAnswer).filter_by(quiz_id=quizId, user_id=user.id, correct=True).count()

    return {
        "quizId": quizId,
        "username": username,
        "totalQuestions": total,
        "correctAnswers": correct,
        "message": "퀴즈 완료. 최종 결과입니다."
    }
