from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.services import recommend_service
from app.schemas.recommend import RecommendedVideoSchema

router = APIRouter(prefix="/recommend", tags=["Recommendation"])

@router.get("/videos", response_model=RecommendedVideoSchema)
def get_random_recommended_video(db: Session = Depends(get_db)):
    video = recommend_service.get_random_video_url(db)
    if not video:
        raise HTTPException(status_code=404, detail="No recommended videos found.")
    return video
