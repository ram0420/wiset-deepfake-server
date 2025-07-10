from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from uuid import uuid4
from app.dependencies import get_db, get_current_user
from app.models import DetectionSession, DetectionResult
from app.schemas.detection import DetectionRunResponse
from tensorflow.keras.models import load_model
from PIL import Image
from io import BytesIO
import numpy as np

router = APIRouter(prefix="/detections", tags=["detection"])
model = load_model("models/deepfake_detector_model.keras")

def predict_deepfake(image: Image.Image) -> float:
    image = image.resize((256, 256))  # ← 모델 input shape에 맞게
    img_array = np.array(image) / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    prob = model.predict(img_array)[0][0]
    return float(prob)


@router.post("/{detectionId}/run", response_model=DetectionRunResponse, status_code=202)
async def run_detection(
    detectionId: str,
    image: UploadFile = File(...),
    timestamp: float = Form(...),
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    session = db.query(DetectionSession).filter_by(id=detectionId, user_id=user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="탐지 세션을 찾을 수 없습니다.")
    if session.status == "completed":
        raise HTTPException(status_code=409, detail="이미 탐지가 완료된 세션입니다.")

    # 이미지 로드 및 예측
    try:
        img = Image.open(BytesIO(await image.read())).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="이미지 파일이 유효하지 않습니다.")

    prob = predict_deepfake(img)
    is_fake = prob > 0.5

    # 결과 저장
    result = DetectionResult(
        detection_id=session.id,
        is_deepfake=is_fake,
        confidence=prob,
        timestamp=timestamp,
        details=f"{timestamp}초 프레임 기반 탐지 결과"
    )
    db.add(result)
    session.status = "completed"
    db.commit()

    return DetectionRunResponse(
        detectionId=session.id,
        message="탐지 요청이 정상적으로 접수되었습니다.",
        estimatedTime=10
    )

from app.schemas.detection import DetectionResultResponse, DetectionResultData

@router.get("/result/{detectionId}", response_model=DetectionResultResponse)
def get_detection_result(detectionId: str, db: Session = Depends(get_db), user = Depends(get_current_user)):
    session = db.query(DetectionSession).filter_by(id=detectionId, user_id=user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="탐지 세션을 찾을 수 없습니다.")

    result = db.query(DetectionResult).filter_by(detection_id=session.id).first()
    if not result:
        raise HTTPException(status_code=404, detail="탐지 결과를 찾을 수 없습니다. 탐지 작업이 완료되지 않았거나 존재하지 않습니다.")

    # timestamp는 details에서 추출하거나 DB에 별도 컬럼으로 두면 좋음
    return DetectionResultResponse(
        detectionId=session.id,
        timestamp=result.timestamp,  # DB에 저장된 float 값 사용
        result=DetectionResultData(
            isDeepfake=result.is_deepfake,
            confidence=result.confidence,
            details=result.details
        )
    )
