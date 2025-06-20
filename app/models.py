 # SQLAlchemy or Tortoise ORM 모델 정의 (User, DetectionJob, Quiz 등)
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.extensions import Base

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    phone = Column(String)

    profile = relationship("UserProfile", back_populates="user")


class UserProfile(Base):
    __tablename__ = "user_profiles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"))
    nickname = Column(String)
    gender = Column(String)
    school_id = Column(Integer, ForeignKey("schools.id"))
    grade = Column(Integer)
    class_num = Column(Integer)
    score = Column(Integer, default=0)

    user = relationship("User", back_populates="profile")
    school = relationship("School")


class School(Base):
    __tablename__ = "schools"
    id = Column(Integer, primary_key=True)
    name = Column(String)


class DetectionSession(Base):
    __tablename__ = "detection_sessions"
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    video_id = Column(String)
    youtube_url = Column(String)
    start_time = Column(Integer)
    end_time = Column(Integer)
    status = Column(String)


class DetectionResult(Base):
    __tablename__ = "detection_results"
    id = Column(Integer, primary_key=True)
    detection_id = Column(String, ForeignKey("detection_sessions.id"))
    is_deepfake = Column(Boolean)
    confidence = Column(Integer)
    details = Column(Text)


class QuizSession(Base):
    __tablename__ = "quiz_sessions"
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"
    id = Column(Integer, primary_key=True)
    quiz_id = Column(String, ForeignKey("quiz_sessions.id"))
    question_number = Column(Integer)
    question = Column(String)
    options = Column(String)  # JSON 문자열로 저장
    correct_answer = Column(String)
    explanation = Column(String)


class QuizAnswer(Base):
    __tablename__ = "quiz_answers"
    id = Column(Integer, primary_key=True)
    quiz_id = Column(String)
    user_id = Column(String)
    question_number = Column(Integer)
    selected_answer = Column(String)
    correct = Column(Boolean)
