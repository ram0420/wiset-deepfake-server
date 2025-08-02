from sqlalchemy.orm import Session
from app.models import DetectionSession, DetectionResult
from uuid import uuid4


def create_detection_session(db: Session, user_id: str) -> DetectionSession:
    """
    새로운 딥페이크 탐지 세션을 생성합니다.
    """
    session = DetectionSession(
        id=str(uuid4()),
        user_id=user_id,
        status="initialized"
    )
    db.add(session)
    db.commit()
    return session


def get_detection_session(db: Session, session_id: str, user_id: str) -> DetectionSession:
    """
    사용자의 특정 탐지 세션을 조회합니다.
    """
    return db.query(DetectionSession).filter_by(id=session_id, user_id=user_id).first()


def mark_session_completed(db: Session, session: DetectionSession):
    """
    탐지 완료로 상태 변경
    """
    session.status = "completed"
    db.commit()


def create_detection_result(
    db: Session,
    session_id: str,
    is_deepfake: bool,
    confidence: float,
    details: str
) -> DetectionResult:
    """
    탐지 결과를 생성 및 저장합니다.
    """
    result = DetectionResult(
        detection_id=session_id,
        is_deepfake=is_deepfake,
        confidence=confidence,
        details=details
    )
    db.add(result)
    db.commit()
    return result


def get_detection_result(db: Session, session_id: str) -> DetectionResult:
    """
    탐지 결과 조회
    """
    return db.query(DetectionResult).filter_by(detection_id=session_id).first()


def delete_detection_session_and_result(db: Session, session_id: str, user_id: str):
    """
    탐지 세션과 해당 결과 및 파일 정리
    """
    session = get_detection_session(db, session_id, user_id)
    if not session:
        return False

    result = get_detection_result(db, session_id)

    # 파일 삭제 로직 (선택)
    if result and result.details:
        import os, re
        base = "./app/static/uploads"
        match1 = re.search(r'캡처: ([\w\-\.]+)', result.details)
        match2 = re.search(r'heatmap: ([\w\-\.]+)', result.details)
        for m in [match1, match2]:
            if m:
                path = os.path.join(base, m.group(1))
                if os.path.exists(path):
                    os.remove(path)

    if result:
        db.delete(result)
    db.delete(session)
    db.commit()
    return True
