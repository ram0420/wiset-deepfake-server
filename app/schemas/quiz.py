# Quiz 요청·응답 스키마

from pydantic import BaseModel
from typing import List


class QuizCreateResponse(BaseModel):
    quizId: str
    message: str


class QuizQuestionResponse(BaseModel):
    quizId: str
    questionNumber: int
    question: str
    options: List[str]


class QuizAnswerRequest(BaseModel):
    questionNumber: int
    answer: str


class QuizAnswerResponse(BaseModel):
    correct: bool
    explanation: str
    score: int
    message: str


class QuizResultResponse(BaseModel):
    quizId: str
    username: str
    totalQuestions: int
    correctAnswers: int
    message: str
