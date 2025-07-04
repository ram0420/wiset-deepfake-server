# app/schemas/main.py

from pydantic import BaseModel
from typing import List


class ButtonPaths(BaseModel):
    myPage: str
    deepfakeDetection: str
    quiz: str


class YoutubeBanner(BaseModel):
    videoId: str
    title: str
    thumbnailUrl: str


class MainPageResponse(BaseModel):
    buttons: ButtonPaths
    youtubeBanner: List[YoutubeBanner]
