# app/schemas/main.py

from pydantic import BaseModel


class ButtonPaths(BaseModel):
    myPage: str
    deepfakeDetection: str
    quiz: str



class MainPageResponse(BaseModel):
    buttons: ButtonPaths
