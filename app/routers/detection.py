from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from uuid import uuid4
from app.dependencies import get_db, get_current_user
from app.schemas.detection import DetectionRunResponse, DetectionResultResponse, DetectionResultData
from app.services import detection_service

import os
import torch
from app.detection_core.inference import run_freqnet_detection
from app.detection_core.Freq_CAM import Freq_CAM_init
from PIL import Image
import re

router = APIRouter(prefix="/detections", tags=["detection"])

MODEL_PATH = "./app/detection_core/freqnet_finetuned.pth"
UPLOAD_DIR = "./app/static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


async def predict_deepfake_freqnet(upload_file: UploadFile) -> tuple[float, bool, str, str]:
    """
    이미지를 저장하고 FreqNet 및 Grad-CAM 실행 후 결과 반환
    """
    filename = f"{uuid4()}.png"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as f:
        f.write(await upload_file.read())

    prediction, result = run_freqnet_detection(
        model_path=MODEL_PATH,
        image_path=file_path,
        cuda=torch.cuda.is_available()
    )
    fake_confidence = result[1]
    is_fake = prediction == 1

    cam_image = Freq_CAM_init(image_save_path=file_path, model_path=MODEL_PATH)
    gradcam_filename = filename.replace(".png", "_gradcam.png")
    gradcam_path = os.path.join(UPLOAD_DIR, gradcam_filename)
    Image.fromarray(cam_image).save(gradcam_path)

    return fake_confidence, is_fake, filename, gradcam_filename


@router.post("/create", status_code=201)
def create_detection_session_endpoint(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    새로운 탐지 세션 생성 
    """
    session = detection_service.create_detection_session(db=db, user_id=user.id)
    return {"detectionId": session.id}


@router.post("/{detectionId}/run", response_model=DetectionRunResponse, status_code=202)
async def run_detection(
    detectionId: str,
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    탐지 수행 및 결과 저장
    """
    session = detection_service.get_detection_session(db, detectionId, user.id)
    if not session:
        raise HTTPException(status_code=404, detail="탐지 세션을 찾을 수 없습니다.")
    if session.status == "completed":
        raise HTTPException(status_code=409, detail="이미 탐지가 완료된 세션입니다.")

    try:
        fake_confidence, is_fake, image_filename, gradcam_filename = await predict_deepfake_freqnet(image)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"탐지 중 오류 발생: {str(e)}")

    details = f"탐지 결과 (캡처: {image_filename}, heatmap: {gradcam_filename})"
    detection_service.create_detection_result(
        db=db,
        session_id=session.id,
        is_deepfake=is_fake,
        confidence=fake_confidence,
        details=details
    )
    detection_service.mark_session_completed(db, session)

    return DetectionRunResponse(
        detectionId=session.id,
        message="탐지 요청이 정상적으로 접수되었습니다.",
        estimatedTime=10
    )


@router.get("/result/{detectionId}", response_model=DetectionResultResponse)
def get_detection_result(
    detectionId: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    탐지 결과와 이미지 URL 반환
    """
    session = detection_service.get_detection_session(db, detectionId, user.id)
    if not session:
        raise HTTPException(status_code=404, detail="탐지 세션을 찾을 수 없습니다.")

    result = detection_service.get_detection_result(db, detectionId)
    if not result:
        raise HTTPException(status_code=404, detail="탐지 결과를 찾을 수 없습니다.")

    image_url, gradcam_url = None, None
    if result.details:
        match1 = re.search(r'캡처: ([\w\-\.]+)', result.details)
        match2 = re.search(r'heatmap: ([\w\-\.]+)', result.details)
        if match1:
            image_url = f"/static/uploads/{match1.group(1)}"
        if match2:
            gradcam_url = f"/static/uploads/{match2.group(1)}"

    return DetectionResultResponse(
        detectionId=session.id,
        result=DetectionResultData(
            isDeepfake=result.is_deepfake,
            confidence=result.confidence,
            imageUrl=image_url,
            gradcamUrl=gradcam_url,
            details=result.details
        )
    )
