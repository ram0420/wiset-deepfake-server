# server/app/utils/jwt_helper.py

from datetime import datetime, timedelta
from jose import jwt, JWTError
from typing import Optional

# 실제 서비스에서는 환경변수로 관리할 것
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    사용자 정보를 담은 JWT 토큰 생성
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> dict:
    """
    JWT 토큰 디코드 및 유효성 검사
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload  # dict: { "sub": user_id, "email": ..., "exp": ... }
    except JWTError as e:
        raise ValueError("Invalid token") from e
