# 공통 의존성(예: DB, 인증) 정의
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.utils.auth import decode_access_token  # ✅ 수정됨
from app.models import User
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# DB 세션 의존성
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 인증된 사용자 가져오기
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_access_token(token)  # ✅ decode_token → decode_access_token으로 변경
    user_id = payload.get("sub") if payload else None
    if not user_id:
        raise HTTPException(status_code=401, detail="토큰이 유효하지 않습니다.")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다.")
    return user
