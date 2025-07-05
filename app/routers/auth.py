# app/routers/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.auth import (
    RegisterRequest, RegisterResponse,
    LoginRequest, LoginResponse,
    FindUsernameRequest, FindUsernameResponse,
    PasswordFindRequest, PasswordFindResponse
)
from app.dependencies import get_db
from app.services import auth_service
from app.utils.auth import create_access_token  # ✅ 수정된 부분

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model=RegisterResponse, status_code=201)
def signup(data: RegisterRequest, db: Session = Depends(get_db)):
    if data.password != data.passwordConfirm:
        raise HTTPException(status_code=422, detail="비밀번호와 비밀번호 확인이 일치하지 않습니다")
    try:
        user = auth_service.register_user(
            db,
            username=data.username,
            password=data.password,
            email=data.email,
            school_code=data.schoolCode,
            gender=data.gender,
            phone=data.phone,
            login_id=data.loginId
        )
        return {"userId": str(user.id), "message": "회원가입 성공"}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = auth_service.authenticate_user(db, data.loginId, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 올바르지 않습니다")

    token = create_access_token({"sub": str(user.id)})  # ✅ JWT 발급 방식 수정
    return {"token": token, "userId": str(user.id)}

@router.post("/findId", response_model=FindUsernameResponse)
def find_id(data: FindUsernameRequest, db: Session = Depends(get_db)):
    user = auth_service.find_user_by_info(
        db,
        name=data.name,
        gender=data.gender,
        school_code=data.schoolCode,
        phone=data.phone,
        email=data.email
    )
    if not user:
        raise HTTPException(status_code=404, detail="입력하신 정보와 일치하는 계정을 찾을 수 없습니다.")
    return {"id": user.login_id}

@router.post("/findPw", response_model=PasswordFindResponse)
def find_pw(data: PasswordFindRequest, db: Session = Depends(get_db)):
    user = auth_service.verify_user_for_pw_reset(
        db, login_id=data.loginId, phone=data.phone, email=data.email
    )
    if not user:
        raise HTTPException(status_code=404, detail="일치하는 사용자를 찾을 수 없습니다.")
    # 실제 서비스에서는 해시값 반환하면 안 됩니다!
    return {"id": user.login_id}  # 또는 임시 비밀번호 발급 로직
