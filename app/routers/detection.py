# from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
# from sqlalchemy.orm import Session
# from uuid import uuid4
# from app.dependencies import get_db, get_current_user
# from app.schemas.detection import DetectionRunResponse, DetectionResultResponse, DetectionResultData
# from app.services import detection_service

# import os
# import torch
# from app.detection_core.inference import run_freqnet_detection
# from app.detection_core.Freq_CAM import Freq_CAM_init
# from PIL import Image
# import re

# router = APIRouter(prefix="/detections", tags=["detection"])

# MODEL_PATH = "./app/detection_core/freqnet_finetuned.pth"
# UPLOAD_DIR = "./app/static/uploads"
# os.makedirs(UPLOAD_DIR, exist_ok=True)


# async def predict_deepfake_freqnet(upload_file: UploadFile) -> tuple[float, bool, str, str]:
#     """
#     이미지를 저장하고 FreqNet 및 Grad-CAM 실행 후 결과 반환
#     """
#     filename = f"{uuid4()}.png"
#     file_path = os.path.join(UPLOAD_DIR, filename)

#     with open(file_path, "wb") as f:
#         f.write(await upload_file.read())

#     prediction, result = run_freqnet_detection(
#         model_path=MODEL_PATH,
#         image_path=file_path,
#         cuda=torch.cuda.is_available()
#     )
#     fake_confidence = result[1]
#     is_fake = prediction == 1

#     cam_image = Freq_CAM_init(image_save_path=file_path, model_path=MODEL_PATH)
#     gradcam_filename = filename.replace(".png", "_gradcam.png")
#     gradcam_path = os.path.join(UPLOAD_DIR, gradcam_filename)
#     Image.fromarray(cam_image).save(gradcam_path)

#     return fake_confidence, is_fake, filename, gradcam_filename


# @router.post("/create", status_code=201)
# def create_detection_session_endpoint(
#     db: Session = Depends(get_db),
#     user=Depends(get_current_user),
# ):
#     """
#     새로운 탐지 세션 생성 
#     """
#     session = detection_service.create_detection_session(db=db, user_id=user.id)
#     return {"detectionId": session.id}


# @router.post("/{detectionId}/run", response_model=DetectionRunResponse, status_code=202)
# async def run_detection(
#     detectionId: str,
#     image: UploadFile = File(...),
#     db: Session = Depends(get_db),
#     user=Depends(get_current_user)
# ):
#     """
#     탐지 수행 및 결과 저장
#     """
#     session = detection_service.get_detection_session(db, detectionId, user.id)
#     if not session:
#         raise HTTPException(status_code=404, detail="탐지 세션을 찾을 수 없습니다.")
#     if session.status == "completed":
#         raise HTTPException(status_code=409, detail="이미 탐지가 완료된 세션입니다.")

#     try:
#         fake_confidence, is_fake, image_filename, gradcam_filename = await predict_deepfake_freqnet(image)
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=f"탐지 중 오류 발생: {str(e)}")

#     details = f"탐지 결과 (캡처: {image_filename}, heatmap: {gradcam_filename})"
#     detection_service.create_detection_result(
#         db=db,
#         session_id=session.id,
#         is_deepfake=is_fake,
#         confidence=fake_confidence,
#         details=details
#     )
#     detection_service.mark_session_completed(db, session)

#     return DetectionRunResponse(
#         detectionId=session.id,
#         message="탐지 요청이 정상적으로 접수되었습니다.",
#         estimatedTime=10
#     )


# @router.get("/result/{detectionId}", response_model=DetectionResultResponse)
# def get_detection_result(
#     detectionId: str,
#     db: Session = Depends(get_db),
#     user=Depends(get_current_user)
# ):
#     """
#     탐지 결과와 이미지 URL 반환
#     """
#     session = detection_service.get_detection_session(db, detectionId, user.id)
#     if not session:
#         raise HTTPException(status_code=404, detail="탐지 세션을 찾을 수 없습니다.")

#     result = detection_service.get_detection_result(db, detectionId)
#     if not result:
#         raise HTTPException(status_code=404, detail="탐지 결과를 찾을 수 없습니다.")

#     image_url, gradcam_url = None, None
#     if result.details:
#         match1 = re.search(r'캡처: ([\w\-\.]+)', result.details)
#         match2 = re.search(r'heatmap: ([\w\-\.]+)', result.details)
#         if match1:
#             image_url = f"/static/uploads/{match1.group(1)}"
#         if match2:
#             gradcam_url = f"/static/uploads/{match2.group(1)}"

#     return DetectionResultResponse(
#         detectionId=session.id,
#         result=DetectionResultData(
#             isDeepfake=result.is_deepfake,
#             confidence=result.confidence,
#             imageUrl=image_url,
#             gradcamUrl=gradcam_url,
#             details=result.details
#         )
#     )


from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
from uuid import uuid4
from app.dependencies import get_db, get_current_user
from app.schemas.detection import DetectionRunResponse, DetectionResultResponse, DetectionResultData
from app.services import detection_service

import os
import io
import re
import gc
import time
import torch
import tempfile
from threading import Lock
from typing import Tuple, Optional, Dict, Any

from app.detection_core.inference import run_freqnet_detection
from app.detection_core.Freq_CAM import Freq_CAM_init
from PIL import Image
import numpy as np

router = APIRouter(prefix="/detections", tags=["detection"])

MODEL_PATH = ".app/detection_core/0904_10epoch.pth"

# ===== 메모리 내 임시 이미지 저장소 (TTL) =====
# 구조: { token: {"orig": bytes, "gradcam": bytes, "exp": epoch_seconds} }
_IMAGE_STORE: Dict[str, Dict[str, Any]] = {}
_IMAGE_STORE_LOCK = Lock()
IMAGE_TTL_SECONDS = 10 * 60  # 10분 (필요시 조정)

def _purge_expired_tokens() -> None:
    now = time.time()
    with _IMAGE_STORE_LOCK:
        expired = [k for k, v in _IMAGE_STORE.items() if v.get("exp", 0) < now]
        for k in expired:
            _IMAGE_STORE.pop(k, None)

def _put_images_to_store(orig_png: bytes, cam_png: bytes) -> str:
    _purge_expired_tokens()
    token = uuid4().hex
    with _IMAGE_STORE_LOCK:
        _IMAGE_STORE[token] = {
            "orig": orig_png,
            "gradcam": cam_png,
            "exp": time.time() + IMAGE_TTL_SECONDS
        }
    return token

def _get_image_from_store(token: str, kind: str) -> Optional[bytes]:
    _purge_expired_tokens()
    with _IMAGE_STORE_LOCK:
        entry = _IMAGE_STORE.get(token)
        if not entry:
            return None
        # TTL 연장(선택): 보기 중 리프레시 대비
        entry["exp"] = time.time() + IMAGE_TTL_SECONDS
        if kind == "orig":
            return entry.get("orig")
        elif kind in ("gradcam", "cam"):
            return entry.get("gradcam")
        return None

# ===== 요청 종료 후 메모리/GPU 정리 =====
async def _cleanup_after():
    try:
        yield
    finally:
        if torch.cuda.is_available():
            try:
                torch.cuda.synchronize()
            except Exception:
                pass
            try:
                torch.cuda.empty_cache()
            except Exception:
                pass
            try:
                # 일부 환경에서 VRAM 조각 수거 도움
                torch.cuda.ipc_collect()
            except Exception:
                pass
        gc.collect()

# ===== 유틸: PIL 이미지를 PNG 바이트로 =====
def _pil_to_png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    try:
        img.save(buf, format="PNG")
        return buf.getvalue()
    finally:
        buf.close()

# ===== 핵심: 디스크 영구 저장 없이 추론 수행 =====
async def _predict_deepfake_freqnet_no_persist(upload_file: UploadFile) -> Tuple[float, bool, bytes, bytes]:
    """
    디스크에 영구 저장 없이:
    - 업로드 바이트를 임시파일로 저장(모델이 경로 인자를 요구하므로)
    - 추론 및 Grad-CAM 생성
    - 임시파일 즉시 제거
    - 원본/Grad-CAM을 PNG 바이트로 반환
    """
    raw = await upload_file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="빈 파일입니다.")

    tmp_path = None
    try:
        # Windows 호환을 위해 delete=False 후 수동 삭제
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(raw)
            tmp.flush()
            tmp_path = tmp.name

        # ---- 모델 추론 (기존 함수가 image_path를 받으므로 임시 경로 사용) ----
        prediction, result = run_freqnet_detection(
            model_path=MODEL_PATH,
            image_path=tmp_path,
            cuda=torch.cuda.is_available()
        )
        fake_confidence: float = float(result[1])
        is_fake: bool = (prediction == 1)

        # ---- Grad-CAM (경로 인자 사용) ----
        cam_array = Freq_CAM_init(image_save_path=tmp_path, model_path=MODEL_PATH)
        if isinstance(cam_array, np.ndarray):
            cam_img = Image.fromarray(cam_array)
        else:
            # 혹시 PIL.Image가 바로 오면 그대로 사용
            cam_img = cam_array  # type: ignore

        # ---- 원본 이미지는 메모리에서 로드 ----
        orig_img = Image.open(io.BytesIO(raw)).convert("RGB")

        # ---- PNG 바이트로 직렬화 (디스크 쓰기 없음) ----
        orig_png = _pil_to_png_bytes(orig_img)
        cam_png = _pil_to_png_bytes(cam_img)

        return fake_confidence, is_fake, orig_png, cam_png

    finally:
        # 임시파일 제거 (영구 저장 방지)
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
        # 큰 바이트 버퍼 참조 해제
        del raw

# ====== 라우팅 ======

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

@router.post("/{detectionId}/run", response_model=DetectionRunResponse, status_code=202, dependencies=[Depends(_cleanup_after)])
async def run_detection(
    detectionId: str,
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    탐지 수행 (디스크 미저장) 및 결과 저장
    - 원본/Grad-CAM 이미지는 메모리 캐시에 TTL로 보관
    - DB details에는 token만 기록 (파일명 저장 안 함)
    """
    session = detection_service.get_detection_session(db, detectionId, user.id)
    if not session:
        raise HTTPException(status_code=404, detail="탐지 세션을 찾을 수 없습니다.")
    if session.status == "completed":
        raise HTTPException(status_code=409, detail="이미 탐지가 완료된 세션입니다.")

    try:
        fake_confidence, is_fake, orig_png, cam_png = await _predict_deepfake_freqnet_no_persist(image)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"탐지 중 오류 발생: {str(e)}")

    # 메모리 캐시에 저장하고 토큰 발급
    token = _put_images_to_store(orig_png, cam_png)

    # 세부정보엔 토큰만 심플하게 저장 (파싱 쉬움)
    details = f"token:{token}"
    detection_service.create_detection_result(
        db=db,
        session_id=session.id,
        is_deepfake=is_fake,
        confidence=fake_confidence,
        details=details
    )
    detection_service.mark_session_completed(db, session)

    # 캐시 방지 헤더 포함
    return JSONResponse(
        content=DetectionRunResponse(
            detectionId=session.id,
            message="탐지 요청이 정상적으로 접수되었습니다.",
            estimatedTime=10
        ).model_dump(),
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )

@router.get("/result/{detectionId}", response_model=DetectionResultResponse, dependencies=[Depends(_cleanup_after)])
def get_detection_result(
    detectionId: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    탐지 결과와 이미지 URL 반환
    - 기존(과거) 세션: details에 파일명이 남아있다면 그 경로도 지원
    - 신규(본 코드): details에 token:xxxx 저장 → 동적 이미지 엔드포인트 URL 반환
    """
    session = detection_service.get_detection_session(db, detectionId, user.id)
    if not session:
        raise HTTPException(status_code=404, detail="탐지 세션을 찾을 수 없습니다.")

    result = detection_service.get_detection_result(db, detectionId)
    if not result:
        raise HTTPException(status_code=404, detail="탐지 결과를 찾을 수 없습니다.")

    image_url = None
    gradcam_url = None

    # 1) 신규 포맷: token:xxxx
    token_match = re.search(r'token:([0-9a-fA-F\-]+)', result.details or "")
    if token_match:
        token = token_match.group(1)
        image_url = f"/detections/image/{token}/orig"
        gradcam_url = f"/detections/image/{token}/gradcam"
    else:
        # 2) 구버전 호환: 파일명 파싱 (이전 세션 대비용)
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

@router.get("/image/{token}/{kind}", dependencies=[Depends(_cleanup_after)])
def get_detection_image(
    token: str,
    kind: str,  # "orig" | "gradcam"
    db: Session = Depends(get_db),  # 접근 제어를 동일하게 유지하려면 의존성 유지
    user=Depends(get_current_user)
):
    """
    메모리에 있는 PNG 이미지를 스트리밍 반환.
    디스크 고정 저장 없이 동작.
    """
    if kind not in ("orig", "gradcam"):
        raise HTTPException(status_code=400, detail="kind는 'orig' 또는 'gradcam'이어야 합니다.")

    data = _get_image_from_store(token, kind)
    if not data:
        # TTL 만료/토큰 없음 → 404
        raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다(만료되었을 수 있음).")

    return StreamingResponse(
        io.BytesIO(data),
        media_type="image/png",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
            "Content-Disposition": f'inline; filename="{kind}.png"'
        },
    )
