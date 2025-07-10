# Pydantic 스키마 정의
# Signup, Login, FindID/PW 스키마

from pydantic import BaseModel, EmailStr, Field

## 회원가입 ##
class RegisterRequest(BaseModel):
    username: str
    gender: str
    schoolCode: str
    loginId: str
    password: str
    passwordConfirm: str
    email: EmailStr
    phone: str

class RegisterResponse(BaseModel):
    loginId: str
    message: str

## 아이디 찾기 ##
class FindUsernameRequest(BaseModel):
    Name: str
    gender: str
    schoolCode: str
    phone: str 
    email: EmailStr

class FindUsernameResponse(BaseModel):
    loginId: str

## 비밀번호 찾기 ##
class PasswordFindRequest(BaseModel):
    loginId: str
    phone: str
    email: EmailStr

class PasswordFindResponse(BaseModel):
    password: str

## 로그인 ##
class LoginRequest(BaseModel):
    loginId: str = Field(..., description="사용자 아이디")
    password: str = Field(..., description="비밀번호")

class LoginResponse(BaseModel):
    token: str
    loginId: str