# 딥페이크 탐지 요청 처리 및 결과 조회
from sqlalchemy.orm import Session
from app.models import DetectionSession, DetectionResult
from uuid import uuid4

def create_detection_session(db: Session, user_id: str, youtube_url: str):
    video_id = youtube_url.split("v=")[-1][-11:]
    session = DetectionSession(
        id=str(uuid4()),
        user_id=user_id,
        video_id=video_id,
        youtube_url=youtube_url,
        status="initialized"
    )
    db.add(session)
    db.commit()
    return session

def update_segment(db: Session, session_id: str, user_id: str, start: int, end: int):
    session = db.query(DetectionSession).filter_by(id=session_id, user_id=user_id).first()
    if not session:
        return None
    session.start_time = start
    session.end_time = end
    db.commit()
    return session

def start_detection_job(db: Session, session_id: str, user_id: str):
    session = db.query(DetectionSession).filter_by(id=session_id, user_id=user_id).first()
    if not session:
        return None
    session.status = "running"
    db.commit()
    return session

def get_detection_result(db: Session, session_id: str, user_id: str):
    session = db.query(DetectionSession).filter_by(id=session_id, user_id=user_id).first()
    if not session:
        return None
    return db.query(DetectionResult).filter_by(detection_id=session_id).first()
