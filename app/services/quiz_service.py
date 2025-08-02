import uuid
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException

from app.models import QuizSession, QuizQuestion, QuizAnswer, UserProfile


# 🔸 문제 시리얼라이즈 (프론트 전달용)
def serialize_question(question: QuizQuestion):
    return {
        "id": question.id,
        "question": question.question,
        "options": question.options,  # 프론트에서 JSON으로 decode
        "image_url": question.image_url,
        "explanation": question.explanation  # ✅ 추가 
    }

def start_quiz(user_id: str, db: Session):
    # 새로운 세션 생성
    session = QuizSession(id=str(uuid.uuid4()), user_id=user_id)
    db.add(session)
    db.commit()

    # 랜덤 10문제 제공
    questions = db.query(QuizQuestion).order_by(func.random()).limit(10).all()

    return {
        "session_id": session.id,
        "questions": [serialize_question(q) for q in questions]
    }


# ✅ 2. 문제 하나 정답 제출
def submit_answer(session_id: str, question_id: int, selected_answer: str, user_id: str, db: Session):
    question = db.query(QuizQuestion).filter_by(id=question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="문제가 존재하지 않습니다.")

    is_correct = (selected_answer == question.correct_answer)

    answer = QuizAnswer(
        quiz_id=session_id,
        user_id=user_id,
        question_id=question_id,
        selected_answer=selected_answer,
        correct=is_correct
    )
    db.add(answer)
    db.commit()

    return {"correct": is_correct}


# ✅ 3. 결과 반환 + 점수 저장 + user_profiles.score에 누적 반영
def get_result(session_id: str, db: Session):
    # 1. 세션 조회
    session = db.query(QuizSession).filter_by(id=session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    # 💬 이미 채점된 세션이면 중복 반영 방지 (score가 이미 저장되어 있음)
    if session.score is not None:
        return {
            "total": db.query(QuizAnswer).filter_by(quiz_id=session_id).count(),
            "correct": session.score // 10,
            "score": session.score,
            "score_string": f"{session.score // 10}/10"
        }

    # 2. 정답 수 계산
    answers = db.query(QuizAnswer).filter_by(quiz_id=session_id).all()
    total = len(answers)
    correct = sum(1 for a in answers if a.correct)
    score = correct * 10

    # 3. 세션에 점수 저장
    session.score = score

    # 4. 유저 프로필 누적 점수 저장 (None 방어 포함)
    profile = db.query(UserProfile).filter_by(user_id=session.user_id).first()
    if profile:
        if profile.score is None:  # 💬 None이면 0으로 초기화
            profile.score = 0
        profile.score += score

    db.commit()

    return {
        "total": total,
        "correct": correct,
        "score": score,
        "score_string": f"{correct}/{total}"
    }

