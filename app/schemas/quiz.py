from pydantic import BaseModel
from typing import List, Optional


# ✅ 퀴즈 문제 1개
class QuizQuestionResponse(BaseModel):
    id: int
    question: str
    options: str  # 프론트에서 JSON.parse()로 디코딩
    image_url: Optional[str] = None
    explanation: Optional[str] = None  # ✅ 추가

    class Config:
        orm_mode = True


# ✅ 퀴즈 시작 응답
class QuizCreateResponse(BaseModel):
    session_id: str
    questions: List[QuizQuestionResponse]


# ✅ 사용자가 정답 제출 시 요청
class QuizAnswerRequest(BaseModel):
    session_id: str
    question_id: int
    selected_answer: str


# ✅ 정답 제출 응답
class QuizAnswerResponse(BaseModel):
    correct: bool


# ✅ 퀴즈 결과 응답
class QuizResultResponse(BaseModel):
    total: int
    correct: int
    score: int
    score_string: str
