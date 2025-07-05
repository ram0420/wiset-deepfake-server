# 랜덤 퀴즈 생성 및 채점

from sqlalchemy.orm import Session
from app.models import QuizSession, QuizQuestion, QuizAnswer
from uuid import uuid4

def create_quiz_session(db: Session, user_id: str) -> str:
    quiz_id = str(uuid4())
    db.add(QuizSession(id=quiz_id, user_id=user_id))

    for i in range(10):
        question = QuizQuestion(
            quiz_id=quiz_id,
            question_number=i + 1,
            question=f"문제 {i + 1}",
            options=["A", "B", "C", "D"],
            correct_answer="A",
            explanation="정답은 A입니다."
        )
        db.add(question)

    db.commit()
    return quiz_id

def get_next_question(db: Session, quiz_id: str, user_id: str):
    answered = db.query(QuizAnswer.question_number).filter_by(quiz_id=quiz_id, user_id=user_id).all()
    answered_set = {q[0] for q in answered}
    return db.query(QuizQuestion).filter(
        QuizQuestion.quiz_id == quiz_id,
        ~QuizQuestion.question_number.in_(answered_set)
    ).order_by(QuizQuestion.question_number).first()

def submit_answer(db: Session, quiz_id: str, user_id: str, question_number: int, selected: str):
    question = db.query(QuizQuestion).filter_by(quiz_id=quiz_id, question_number=question_number).first()
    if not question:
        return None, 0

    correct = question.correct_answer == selected
    db.add(QuizAnswer(
        quiz_id=quiz_id,
        user_id=user_id,
        question_number=question_number,
        selected_answer=selected,
        correct=correct
    ))
    db.commit()

    score = db.query(QuizAnswer).filter_by(quiz_id=quiz_id, user_id=user_id, correct=True).count() * 10
    return correct, score, question.explanation

def get_quiz_result(db: Session, quiz_id: str, user_id: str):
    total = db.query(QuizQuestion).filter_by(quiz_id=quiz_id).count()
    correct = db.query(QuizAnswer).filter_by(quiz_id=quiz_id, user_id=user_id, correct=True).count()
    return total, correct
