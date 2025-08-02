from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True)  # 내부 식별자
    login_id = Column(String, unique=True, index=True)  # 변수명과 컬럼명 일치
    password_hash = Column(String)  # 비밀번호 해시
    email = Column(String, index=True)  # 이메일
    username = Column(String)  # 사용자 이름
    phone = Column(String)  # 전화번호

    profile = relationship("UserProfile", back_populates="user", uselist=False )  # 1:1 연결된 프로필
    quiz_sessions = relationship("QuizSession", back_populates="user")

class UserProfile(Base):
    __tablename__ = "user_profiles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"))

    gender = Column(String)
    score = Column(Integer, default=0)

    school_id = Column(Integer, ForeignKey("schools.id"))  # ✅ FK 연결
    grade = Column(Integer)
    class_num = Column(Integer)


    # ✅ 사용자 계정 정보 (User 테이블 연결)
    user = relationship("User", back_populates="profile")
    school = relationship("School", back_populates="students") #역참조


class School(Base):
    __tablename__ = "schools"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True)  # 예: "한국중0101"
    name = Column(String)               # 예: "한국중"

    students = relationship("UserProfile", back_populates="school")  # ✅ 역참조

##########################################################################################3


class DetectionSession(Base):
    __tablename__ = "detection_sessions"
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    status = Column(String)

    

class DetectionResult(Base):
    __tablename__ = "detection_results"
    id = Column(Integer, primary_key=True)
    detection_id = Column(String, ForeignKey("detection_sessions.id"))
    is_deepfake = Column(Boolean, nullable=False)
    confidence = Column(Float, nullable=False)
    details = Column(Text, nullable=True)  # ← "abc.png, abc_gradcam.png" 등


##########################################################################################3

class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(String, nullable=False)
    options = Column(Text, nullable=False)  # JSON 문자열
    correct_answer = Column(String, nullable=False)
    image_url = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)


class QuizSession(Base):
    __tablename__ = "quiz_sessions"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    score = Column(Integer, nullable=True)  # 오늘 맞춘 점수 (0~100)

    user = relationship("User", back_populates="quiz_sessions")
    answers = relationship("QuizAnswer", back_populates="session", cascade="all, delete-orphan")


class QuizAnswer(Base):
    __tablename__ = "quiz_answers"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(String, ForeignKey("quiz_sessions.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("quiz_questions.id"), nullable=False)
    selected_answer = Column(Text, nullable=False)
    correct = Column(Boolean, nullable=False)

    session = relationship("QuizSession", back_populates="answers")
    question = relationship("QuizQuestion")

##########################################################################################3

class RecommendedVideo(Base):
    __tablename__ = "recommended_videos"

    id = Column(Integer, primary_key=True, index=True)
    youtube_url = Column(String, nullable=False)