# API 라우터 모듈
# /api/v1/auth 라우터 (signup, login, find-id, find-pw)

# auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.auth import (
    RegisterRequest, RegisterResponse,
    LoginRequest, LoginResponse,
    FindUsernameRequest, FindUsernameResponse,
    PasswordResetRequest, PasswordResetResponse,
    PasswordFindRequest, PasswordFindResponse
)
from app.dependencies import get_db
from app.services import auth_service

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
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = auth_service.create_login_token(user)
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
    return {"id": user.password_hash}  # 보안상 실제 사용 시 제거 필요

# @router.post("/resetPw", response_model=PasswordResetResponse)
# def reset_pw(data: PasswordResetRequest, db: Session = Depends(get_db)):
#     user = auth_service.verify_user_for_pw_reset(
#         db, login_id=data.loginId, email=data.email
#     )
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found or email mismatch")
#     return {"message": "비밀번호 재설정 링크를 이메일로 전송하였습니다."}
