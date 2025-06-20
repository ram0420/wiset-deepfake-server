# Pydantic 스키마 정의
# Signup, Login, FindID/PW 스키마

from pydantic import BaseModel, EmailStr, Field

class LoginRequest(BaseModel):
    username: str = Field(..., description="사용자 아이디")
    password: str = Field(..., description="비밀번호")

class LoginResponse(BaseModel):
    token: str
    userId: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    email: EmailStr
    school: str
    grade: int
    classNumber: int

class RegisterResponse(BaseModel):
    userId: str
    message: str

class FindUsernameRequest(BaseModel):
    email: EmailStr

class FindUsernameResponse(BaseModel):
    username: str

class PasswordResetRequest(BaseModel):
    username: str
    email: EmailStr

class PasswordResetResponse(BaseModel):
    message: str
