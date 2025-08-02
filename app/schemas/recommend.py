from pydantic import BaseModel

class RecommendedVideoSchema(BaseModel):
    youtube_url: str

    class Config:
        orm_mode = True
