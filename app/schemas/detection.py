# Detection 요청·결과 스키마

from pydantic import BaseModel
from typing import Optional


class DetectionRunResponse(BaseModel):
    detectionId: str
    message: str
    estimatedTime: int


class DetectionResultData(BaseModel):
    isDeepfake: bool
    confidence: float
    details: str


class DetectionResultResponse(BaseModel):
    detectionId: str
    timestamp: str 
    result: DetectionResultData
