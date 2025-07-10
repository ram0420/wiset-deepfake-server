# 딥페이크 탐지 요청 처리 및 결과 조회
from sqlalchemy.orm import Session
from app.models import DetectionSession, DetectionResult
from uuid import uuid4

def create_detection_session(db: Session, user_id: str, video_id: str):
    session = DetectionSession(
        id=str(uuid4()),
        user_id=user_id,
        video_id=video_id,
        status="initialized"
    )
    db.add(session)
    db.commit()
    return session
