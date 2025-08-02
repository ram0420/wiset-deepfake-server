import random
from sqlalchemy.orm import Session
from app.models import RecommendedVideo
from app.services import recommend_service

def get_random_video_url(db: Session):
    all_videos = db.query(RecommendedVideo).all()
    if not all_videos:
        return None
    return random.choice(all_videos)
