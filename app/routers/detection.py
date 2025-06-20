# # /api/v1/detection 라우터 (start, result)
# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session
# from uuid import uuid4
# from app.dependencies import get_db, get_current_user
# from app.models import DetectionSession, DetectionResult
# from app.schemas.detection import (
#     YoutubeUrlRequest, YoutubeVideoInfoResponse,
#     TimeSegmentRequest, DetectionRunResponse,
#     DetectionResultResponse, DetectionResultData
# )

# router = APIRouter(prefix="/detections", tags=["detection"])


# @router.post("", response_model=YoutubeVideoInfoResponse)
# def get_youtube_info(data: YoutubeUrlRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
#     if "youtube.com" not in data.youtubeUrl and "youtu.be" not in data.youtubeUrl:
#         raise HTTPException(status_code=400, detail="유효하지 않은 유튜브 URL입니다.")

#     video_id = data.youtubeUrl.split("v=")[-1][-11:]  # 단순 추출
#     session = DetectionSession(
#         id=str(uuid4()),
#         user_id=user.id,
#         video_id=video_id,
#         youtube_url=data.youtubeUrl,
#         status="initialized"
#     )
#     db.add(session)
#     db.commit()

#     return YoutubeVideoInfoResponse(
#         videoId=video_id,
#         title="샘플 영상 제목",
#         duration=300,
#         thumbnailUrl=f"https://img.youtube.com/vi/{video_id}/0.jpg"
#     )


# @router.put("/{detectionId}/segments")
# def set_detection_segment(detectionId: str, data: TimeSegmentRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
#     if data.startTime < 0 or data.endTime <= data.startTime:
#         raise HTTPException(status_code=400, detail="시작 시간 또는 종료 시간이 유효하지 않습니다.")

#     session = db.query(DetectionSession).filter_by(id=detectionId, user_id=user.id).first()
#     if not session:
#         raise HTTPException(status_code=404, detail="탐지 세션을 찾을 수 없습니다.")

#     session.start_time = data.startTime
#     session.end_time = data.endTime
#     db.commit()

#     return {
#         "detectionId": detectionId,
#         "startTime": data.startTime,
#         "endTime": data.endTime,
#         "message": "탐지 구간이 성공적으로 설정되었습니다."
#     }


# @router.post("/{detectionId}/run", response_model=DetectionRunResponse, status_code=202)
# def start_detection(detectionId: str, data: TimeSegmentRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
#     session = db.query(DetectionSession).filter_by(id=detectionId, user_id=user.id).first()
#     if not session:
#         raise HTTPException(status_code=404, detail="해당 탐지 세션을 찾을 수 없습니다.")

#     if session.status in ["running", "completed"]:
#         raise HTTPException(status_code=409, detail="이미 탐지가 진행 중이거나 완료된 세션입니다.")

#     if data.startTime < 0 or data.endTime <= data.startTime:
#         raise HTTPException(status_code=400, detail="요청이 잘못되었거나 시간 범위가 유효하지 않습니다.")

#     session.start_time = data.startTime
#     session.end_time = data.endTime
#     session.status = "running"
#     db.commit()

#     return DetectionRunResponse(
#         detectionId=detectionId,
#         message="탐지 요청이 정상적으로 접수되었습니다.",
#         estimatedTime=10
#     )


# @router.get("/result/{detectionId}", response_model=DetectionResultResponse)
# def get_detection_result(detectionId: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
#     session = db.query(DetectionSession).filter_by(id=detectionId, user_id=user.id).first()
#     if not session:
#         raise HTTPException(status_code=404, detail="탐지 세션을 찾을 수 없습니다.")

#     result = db.query(DetectionResult).filter_by(detection_id=session.id).first()
#     if not result:
#         raise HTTPException(status_code=404, detail="탐지 결과를 찾을 수 없습니다. 탐지 작업이 완료되지 않았거나 존재하지 않습니다.")

#     return DetectionResultResponse(
#         detectionId=session.id,
#         videoId=session.video_id,
#         startTime=session.start_time,
#         endTime=session.end_time,
#         result=DetectionResultData(
#             isDeepfake=result.is_deepfake,
#             confidence=result.confidence,
#             details=result.details
#         )
#     )


from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from uuid import uuid4
from app.dependencies import get_db, get_current_user
from app.models import DetectionSession, DetectionResult
from app.schemas.detection import (
    YoutubeUrlRequest, YoutubeVideoInfoResponse,
    TimeSegmentRequest, DetectionRunResponse,
    DetectionResultResponse, DetectionResultData
)

from tensorflow.keras.models import load_model
from PIL import Image
from io import BytesIO
import numpy as np

router = APIRouter(prefix="/detections", tags=["detection"])

# 모델 로드 (모듈 로딩 시 1회)
model = load_model("models/deepfake_detector_model.keras")

# 추론 함수
def predict_deepfake(image: Image.Image) -> float:
    image = image.resize((224, 224))
    img_array = np.array(image) / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    prob = model.predict(img_array)[0][0]
    return float(prob)


@router.post("", response_model=YoutubeVideoInfoResponse)
def get_youtube_info(data: YoutubeUrlRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if "youtube.com" not in data.youtubeUrl and "youtu.be" not in data.youtubeUrl:
        raise HTTPException(status_code=400, detail="유효하지 않은 유튜브 URL입니다.")

    video_id = data.youtubeUrl.split("v=")[-1][-11:]  # 단순 추출
    session = DetectionSession(
        id=str(uuid4()),
        user_id=user.id,
        video_id=video_id,
        youtube_url=data.youtubeUrl,
        status="initialized"
    )
    db.add(session)
    db.commit()

    return YoutubeVideoInfoResponse(
        videoId=video_id,
        title="샘플 영상 제목",
        duration=300,
        thumbnailUrl=f"https://img.youtube.com/vi/{video_id}/0.jpg"
    )


@router.put("/{detectionId}/segments")
def set_detection_segment(detectionId: str, data: TimeSegmentRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if data.startTime < 0 or data.endTime <= data.startTime:
        raise HTTPException(status_code=400, detail="시작 시간 또는 종료 시간이 유효하지 않습니다.")

    session = db.query(DetectionSession).filter_by(id=detectionId, user_id=user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="탐지 세션을 찾을 수 없습니다.")

    session.start_time = data.startTime
    session.end_time = data.endTime
    db.commit()

    return {
        "detectionId": detectionId,
        "startTime": data.startTime,
        "endTime": data.endTime,
        "message": "탐지 구간이 성공적으로 설정되었습니다."
    }


@router.post("/{detectionId}/run", response_model=DetectionRunResponse, status_code=202)
def start_detection(detectionId: str, data: TimeSegmentRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    session = db.query(DetectionSession).filter_by(id=detectionId, user_id=user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="해당 탐지 세션을 찾을 수 없습니다.")

    if session.status in ["running", "completed"]:
        raise HTTPException(status_code=409, detail="이미 탐지가 진행 중이거나 완료된 세션입니다.")

    if data.startTime < 0 or data.endTime <= data.startTime:
        raise HTTPException(status_code=400, detail="요청이 잘못되었거나 시간 범위가 유효하지 않습니다.")

    session.start_time = data.startTime
    session.end_time = data.endTime
    session.status = "running"
    db.commit()

    return DetectionRunResponse(
        detectionId=detectionId,
        message="탐지 요청이 정상적으로 접수되었습니다.",
        estimatedTime=10
    )


@router.get("/result/{detectionId}", response_model=DetectionResultResponse)
def get_detection_result(detectionId: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    session = db.query(DetectionSession).filter_by(id=detectionId, user_id=user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="탐지 세션을 찾을 수 없습니다.")

    result = db.query(DetectionResult).filter_by(detection_id=session.id).first()
    if not result:
        raise HTTPException(status_code=404, detail="탐지 결과를 찾을 수 없습니다. 탐지 작업이 완료되지 않았거나 존재하지 않습니다.")

    return DetectionResultResponse(
        detectionId=session.id,
        videoId=session.video_id,
        startTime=session.start_time,
        endTime=session.end_time,
        result=DetectionResultData(
            isDeepfake=result.is_deepfake,
            confidence=result.confidence,
            details=result.details
        )
    )


# ✅ 이미지 업로드 후 추론 (Flutter에서 전송할 경우 사용할 수 있음)
@router.post("/{detectionId}/predict-image")
async def predict_image_for_detection(detectionId: str, image: UploadFile = File(...), db: Session = Depends(get_db), user=Depends(get_current_user)):
    session = db.query(DetectionSession).filter_by(id=detectionId, user_id=user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="탐지 세션을 찾을 수 없습니다.")

    img = Image.open(BytesIO(await image.read())).convert("RGB")
    prob = predict_deepfake(img)

    # DB에 결과 저장 예시 (선택)
    result = DetectionResult(
        detection_id=detectionId,
        is_deepfake=prob > 0.5,
        confidence=prob,
        details="이미지 한 장 기반 탐지 결과"
    )
    db.add(result)
    session.status = "completed"
    db.commit()

    return {"fake_probability": prob}