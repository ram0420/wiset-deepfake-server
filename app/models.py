from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
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
    img_id = Column(String)
    status = Column(String)
    

class DetectionResult(Base):
    __tablename__ = "detection_results"
    id = Column(Integer, primary_key=True)
    detection_id = Column(String, ForeignKey("detection_sessions.id"))
    is_deepfake = Column(Boolean)
    confidence = Column(Float)  # ← float로 변경
    timestamp = Column(Float)   # ← 새로 추가
    details = Column(Text)

##########################################################################################3

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
