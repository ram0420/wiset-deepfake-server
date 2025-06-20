# Profile 조회·수정 스키마

# server/app/schemas/user.py

from pydantic import BaseModel
from typing import Optional, List


# 1. 사용자 정보 조회 응답
class MyInfoResponse(BaseModel):
    userId: str         # UUID
    loginId: str        # 로그인용 ID (이메일 기반)
    name: str           # 사용자 실명
    gender: str
    schoolCode: str
    phone: str
    email: str


# 2. 사용자 정보 수정 요청
class UpdateMyInfoRequest(BaseModel):
    name: Optional[str] = None
    gender: Optional[str] = None
    loginId: Optional[str] = None
    password: Optional[str] = None
    passwordConfirm: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


# 3. 사용자 정보 수정 응답
class UpdateResponse(BaseModel):
    message: str


# 4. 클래스 랭킹 개별 항목
class RankInfo(BaseModel):
    userId: str
    username: str
    score: int
    rank: int


# 5. 클래스 랭킹 전체 응답
class ClassRankingResponse(BaseModel):
    classInfo: dict  # {"schoolName": str, "grade": int, "classNumber": int}
    myRank: RankInfo
    ranking: List[RankInfo]
