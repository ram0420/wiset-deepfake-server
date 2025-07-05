 # 비즈니스 로직 레이어

# 회원가입·로그인·ID/PW 찾기 구현

from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app.models import User
from app.utils.auth import create_access_token

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def authenticate_user(db: Session, login_id: str, password: str):
    user = db.query(User).filter(User.email == login_id).first()
    if not user or not verify_password(password, user.password_hash):
        return None
    return user

def register_user(db: Session, user_data):
    # user_data: dict or schema object
    hashed_pw = get_password_hash(user_data.password)
    user = User(email=user_data.loginId, password_hash=hashed_pw, phone=user_data.phone)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def create_token(user: User):
    return create_access_token({"sub": str(user.id), "email": user.email})
