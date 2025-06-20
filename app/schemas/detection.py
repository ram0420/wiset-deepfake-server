# Detection 요청·결과 스키마

from pydantic import BaseModel
from typing import Optional


class YoutubeUrlRequest(BaseModel):
    youtubeUrl: str


class YoutubeVideoInfoResponse(BaseModel):
    videoId: str
    title: str
    duration: int
    thumbnailUrl: str


class TimeSegmentRequest(BaseModel):
    startTime: int
    endTime: int


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
    videoId: str
    startTime: int
    endTime: int
    result: DetectionResultData
