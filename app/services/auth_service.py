
import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException
from passlib.context import CryptContext
from app.models import User, UserProfile, School
from app.utils.auth import create_access_token

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def authenticate_user(db: Session, login_id: str, password: str):
    user = db.query(User).filter(User.login_id == login_id).first()  # ✅ 수정됨
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


def register_user(
    db: Session,
    username: str,
    password: str,
    email: str,
    school_code: str,
    gender: str,
    phone: str,
    login_id: str
):
    # 1. 중복 ID 확인
    if db.query(User).filter(User.login_id == login_id).first():
        raise ValueError("이미 사용 중인 아이디입니다.")

    user_id = str(uuid.uuid4())
    hashed_pw = get_password_hash(password)

    # 1. 중복 ID 확인
    user_in_session = db.query(User).filter(User.login_id == login_id).first()

    if user_in_session:
        raise ValueError("이미 사용 중인 아이디입니다.")

    # 2. User 생성
    user = User(
        id=user_id,
        login_id=login_id,
        password_hash=hashed_pw,
        email=email,
        username=username,
        phone=phone
    )
    db.add(user)
    db.flush()  # user.id 확보용

    # 3. School 확인
    school = db.query(School).filter(School.code == school_code).first()
    if not school:
        raise ValueError("유효하지 않은 학교 코드입니다.")


    # 4. 학년 / 반 정보 파싱
    try:
        grade = int(school_code[-4:-2])
        class_num = int(school_code[-2:])
    except ValueError:
        raise ValueError("학교 코드에서 학년/반 정보를 추출할 수 없습니다.")

   
    # 6. UserProfile 생성
    profile = UserProfile(
    user_id=user.id,
    gender=gender,
    score=0,
    school_id=school.id,
    grade=grade,
    class_num=class_num
    )
    db.add(profile)

    db.commit()
    db.refresh(user)

    return user
