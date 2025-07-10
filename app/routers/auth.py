from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.auth import (
    RegisterRequest, RegisterResponse,
    LoginRequest, LoginResponse,
    FindUsernameRequest, FindUsernameResponse,
    PasswordFindRequest, PasswordFindResponse
)
from app.models import User
from app.dependencies import get_db
from app.services import auth_service
from app.utils.auth import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=RegisterResponse, status_code=201)
def signup(data: RegisterRequest, db: Session = Depends(get_db)):
    if data.password != data.passwordConfirm:
        raise HTTPException(
            status_code=422,
            detail="비밀번호와 비밀번호 확인이 일치하지 않습니다"
        )
    try:
        user = auth_service.register_user(
            db,
            username=data.username,
            password=data.password,
            email=data.email,
            school_code=data.schoolCode,
            gender=data.gender,
            phone=data.phone,
            login_id=data.loginId  # 로그인용 ID
        )
        return {
            "loginId": user.loginId,  # 수정: 정확한 필드명(loginId) 반환
            "message": "회원가입 성공"
        }
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/check-user-id")
def check_user_id(user_id: str, db: Session = Depends(get_db)):
    # User 모델의 로그인 ID 필드는 loginId 입니다.
    exists = db.query(User).filter(User.loginId == user_id).first()
    return {
        "isDuplicate": bool(exists),
        "message": "이미 사용 중인 아이디입니다." if exists else "사용 가능한 아이디입니다."
    }


@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = auth_service.authenticate_user(
        db,
        login_id=data.loginId,  # 로그인용 ID 사용 (User.loginId)
        password=data.password
    )
    if not user:
        raise HTTPException(
            status_code=401, 
            detail="아이디 또는 비밀번호가 올바르지 않습니다."
        )

    token = create_access_token({"sub": str(user.id)})
    return {
        "token": token,
        "loginId": user.loginId  # 수정: 정확한 필드명(loginId) 반환
    }
