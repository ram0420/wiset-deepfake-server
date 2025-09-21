# from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
# from fastapi.responses import StreamingResponse
# from sqlalchemy.orm import Session
# from app.dependencies import get_db, get_current_user
# from app.schemas.detection import (
#     DetectionRunResponse,
#     DetectionResultResponse,
#     DetectionResultData,
# )
# from app.services import detection_service

# import io
# import os
# import re
# import time
# import tempfile
# from threading import Lock
# from typing import Dict, Any, Optional, Tuple

# import torch
# import numpy as np
# from PIL import Image

# from app.detection_core.inference import run_freqnet_detection
# from app.detection_core.Freq_CAM import Freq_CAM_init

# router = APIRouter(prefix="/detections", tags=["detection"])

# # ===== 설정 =====
# MODEL_PATH = "./app/detection_core/0904_10epoch.pth"

# # ===== 메모리 내 임시 이미지 저장소 (TTL) =====
# # 구조: { token: {"orig": bytes, "gradcam": bytes, "exp": epoch_seconds} }
# _IMAGE_STORE: Dict[str, Dict[str, Any]] = {}
# _IMAGE_STORE_LOCK = Lock()
# IMAGE_TTL_SECONDS = 10 * 60  # 10분 (필요시 조정)

# def _purge_expired_tokens() -> None:
#     now = time.time()
#     with _IMAGE_STORE_LOCK:
#         expired = [k for k, v in _IMAGE_STORE.items() if v.get("exp", 0) < now]
#         for k in expired:
#             _IMAGE_STORE.pop(k, None)

# def _put_images_to_store(orig_png: bytes, cam_png: bytes) -> str:
#     from uuid import uuid4
#     token = uuid4().hex
#     with _IMAGE_STORE_LOCK:
#         _IMAGE_STORE[token] = {
#             "orig": orig_png,
#             "gradcam": cam_png,
#             "exp": time.time() + IMAGE_TTL_SECONDS,
#         }
#     return token

# def _get_image_from_store(token: str, kind: str) -> Optional[bytes]:
#     _purge_expired_tokens()
#     with _IMAGE_STORE_LOCK:
#         entry = _IMAGE_STORE.get(token)
#         if not entry:
#             return None
#         # 조회 시 TTL 연장(선택)
#         entry["exp"] = time.time() + IMAGE_TTL_SECONDS
#         if kind == "orig":
#             return entry.get("orig")
#         elif kind in ("gradcam", "cam"):
#             return entry.get("gradcam")
#         return None

# def _pil_to_png_bytes(img_pil: Image.Image) -> bytes:
#     buf = io.BytesIO()
#     img_pil.save(buf, format="PNG")
#     return buf.getvalue()

# # ===== 코어: 디스크 영구 저장 없이 추론 수행 =====
# async def _predict_deepfake_freqnet_no_persist(upload_file: UploadFile) -> Tuple[float, bool, bytes, bytes]:
#     """
#     디스크에 영구 저장하지 않고:
#     - 업로드 이미지를 메모리에서 PNG 정규화
#     - Windows 호환을 위해 닫힌 임시파일 경로(tmp_path)를 만들고 여기에만 잠시 기록
#     - 모델 추론 및 Grad-CAM 생성
#     - 임시파일 즉시 삭제
#     - 원본/Grad-CAM을 PNG 바이트로 반환
#     """
#     # 업로드 읽기
#     raw = await upload_file.read()
#     if not raw:
#         raise HTTPException(status_code=400, detail="빈 파일입니다.")

#     # 원본을 PIL로 파싱 (유효성 체크 겸 RGB 변환)
#     try:
#         orig_img = Image.open(io.BytesIO(raw)).convert("RGB")
#     except Exception:
#         raise HTTPException(status_code=415, detail="유효한 이미지 파일이 아닙니다.")

#     # 메모리에서 PNG 바이트로 정규화
#     orig_png = _pil_to_png_bytes(orig_img)

#     tmp_path = None
#     try:
#         # Windows: NamedTemporaryFile(delete=False) 후 수동 삭제
#         with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
#             tmp_path = tmp.name
#         with open(tmp_path, "wb") as f:
#             f.write(orig_png)

#         # ---- 모델 추론 (기존 함수가 image_path를 받으므로 임시 경로 사용) ----
#         prediction, result = run_freqnet_detection(
#             model_path=MODEL_PATH,
#             image_path=tmp_path,
#             cuda=torch.cuda.is_available()
#         )
#         fake_confidence: float = float(result[1])
#         is_fake: bool = (prediction == 1)

#         # ---- Grad-CAM 생성 ----
#         cam_array = Freq_CAM_init(image_save_path=tmp_path, model_path=MODEL_PATH)
#         if isinstance(cam_array, Image.Image):
#             cam_img = cam_array
#         else:
#             cam_img = Image.fromarray(np.asarray(cam_array))
#         cam_png = _pil_to_png_bytes(cam_img)

#         return fake_confidence, is_fake, orig_png, cam_png

#     finally:
#         # 임시파일 제거 (영구 저장 방지)
#         if tmp_path and os.path.exists(tmp_path):
#             try:
#                 os.remove(tmp_path)
#             except Exception:
#                 pass

# # ===== 라우팅 =====

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
#     image: UploadFile = File(None),
#     file: UploadFile = File(None),  # 프런트가 'file' 필드명을 쓰는 경우 호환
#     db: Session = Depends(get_db),
#     user=Depends(get_current_user),
# ):
#     """
#     탐지 수행 (디스크 미저장) 및 결과 저장
#     - 원본/Grad-CAM 이미지는 메모리 캐시에 TTL로 보관
#     - DB details에는 token만 기록 (파일명 저장 안 함)
#     """
#     # 세션 확인
#     session = detection_service.get_detection_session(db, detectionId, user.id)
#     if not session:
#         raise HTTPException(status_code=404, detail="탐지 세션을 찾을 수 없습니다.")
#     if getattr(session, "status", None) == "completed":
#         raise HTTPException(status_code=409, detail="이미 탐지가 완료된 세션입니다.")

#     upload = image or file
#     if not upload:
#         raise HTTPException(status_code=400, detail="이미지 파일이 필요합니다. (form field: image)")

#     try:
#         fake_confidence, is_fake, orig_png, cam_png = await _predict_deepfake_freqnet_no_persist(upload)
#     except HTTPException:
#         raise
#     except Exception as e:
#         # 내부 예외는 500으로 래핑
#         print(f"[run_detection] error for {detectionId}: {e}")
#         raise HTTPException(status_code=500, detail="탐지 처리 중 오류가 발생했습니다.")

#     # 메모리 캐시에 저장하고 토큰 발급
#     token = _put_images_to_store(orig_png, cam_png)

#     # DB에 token 저장
#     details = f"token={token}"
#     detection_service.create_detection_result(
#         db=db,
#         session_id=session.id,
#         is_deepfake=is_fake,
#         confidence=fake_confidence,
#         details=details
#     )
#     detection_service.mark_session_completed(db, session)
#     try:
#         db.commit()
#     except Exception:
#         db.rollback()
#         raise

#     # 응답
#     return DetectionRunResponse(
#         detectionId=session.id,
#         message="탐지 요청이 정상적으로 접수되었습니다.",
#         estimatedTime=0
#     )

# @router.get("/result/{detectionId}", response_model=DetectionResultResponse)
# def get_detection_result(
#     detectionId: str,
#     db: Session = Depends(get_db),
#     user=Depends(get_current_user)
# ):
#     """
#     탐지 결과 + 이미지 URL 반환
#     - details에 token=xxxx 저장 → 동적 이미지 엔드포인트 URL 생성
#     """
#     session = detection_service.get_detection_session(db, detectionId, user.id)
#     if not session:
#         raise HTTPException(status_code=404, detail="탐지 세션을 찾을 수 없습니다.")

#     result = detection_service.get_detection_result(db, detectionId)
#     if not result:
#         # 기존 클라이언트가 폴링을 404 기준으로 구현했다면 유지
#         raise HTTPException(status_code=404, detail="탐지 결과를 찾을 수 없습니다.")

#     token = None
#     if result.details:
#         m = re.search(r"token=([a-f0-9]+)", result.details)
#         token = m.group(1) if m else None

#     image_url = f"/detections/image?kind=orig&t={token}" if token else None
#     gradcam_url = f"/detections/image?kind=gradcam&t={token}" if token else None

#     return DetectionResultResponse(
#         detectionId=session.id if hasattr(session, "id") else detectionId,
#         result=DetectionResultData(
#             isDeepfake=bool(result.is_deepfake),
#             confidence=float(result.confidence),
#             imageUrl=image_url,
#             gradcamUrl=gradcam_url,
#             details=result.details
#         )
#     )

# @router.get("/image")
# def get_image(kind: str, t: str):
#     """
#     메모리에 있는 PNG 이미지를 스트리밍 반환.
#     디스크 고정 저장 없이 동작.
#     """
#     if kind not in ("orig", "gradcam"):
#         raise HTTPException(status_code=400, detail="kind must be 'orig' or 'gradcam'")

#     data = _get_image_from_store(t, kind)
#     if not data:
#         # TTL 만료/토큰 없음 → 404
#         raise HTTPException(status_code=404, detail="이미지가 만료되었거나 토큰이 유효하지 않습니다.")

#     return StreamingResponse(
#         io.BytesIO(data),
#         media_type="image/png",
#         headers={
#             "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
#             "Pragma": "no-cache",
#             "Expires": "0",
#             "Content-Disposition": f'inline; filename="{kind}.png"',
#         },
#     )

# app/routers/detection.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.schemas.detection import (
    DetectionRunResponse,
    DetectionResultResponse,
    DetectionResultData,
)
from app.services import detection_service

import io
import os
import re
import time
import tempfile
from threading import Lock
from typing import Dict, Any, Optional, Tuple

# ===== 저메모리 환경 권장 설정 (Render Free) =====
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import torch
import numpy as np
from PIL import Image

from app.detection_core.inference import run_freqnet_detection
from app.detection_core.Freq_CAM import Freq_CAM_init

router = APIRouter(prefix="/detections", tags=["detection"])

# ===== 설정 =====
MODEL_PATH = "./app/detection_core/0904_10epoch.pth"

# 메모리/성능 튜닝(환경변수로 조정 가능)
DISABLE_CAM = os.getenv("DISABLE_CAM", "1") == "1"   # 기본: CAM 사전생성 끔(온디맨드)
MAX_IMG_DIM = int(os.getenv("MAX_IMG_DIM", "384"))   # 추론 입력 리사이즈 상한(px)
CAM_MAX_DIM = int(os.getenv("CAM_MAX_DIM", "256"))   # CAM 계산 전용 더 작은 상한(px)
try:
    torch.set_num_threads(int(os.getenv("TORCH_NUM_THREADS", "1")))
except Exception:
    pass

# ===== 메모리 내 임시 이미지 저장소 (TTL) =====
# 구조: { token: {"orig": bytes, "gradcam": bytes|None, "exp": epoch_seconds} }
_IMAGE_STORE: Dict[str, Dict[str, Any]] = {}
_IMAGE_STORE_LOCK = Lock()
IMAGE_TTL_SECONDS = 10 * 60  # 10분 (필요시 조정)

def _purge_expired_tokens() -> None:
    now = time.time()
    with _IMAGE_STORE_LOCK:
        expired = [k for k, v in _IMAGE_STORE.items() if v.get("exp", 0) < now]
        for k in expired:
            _IMAGE_STORE.pop(k, None)

def _put_images_to_store(orig_png: bytes, cam_png: Optional[bytes]) -> str:
    from uuid import uuid4
    token = uuid4().hex
    with _IMAGE_STORE_LOCK:
        _IMAGE_STORE[token] = {
            "orig": orig_png,
            "gradcam": cam_png,
            "exp": time.time() + IMAGE_TTL_SECONDS,
        }
    return token

def _update_cam_in_store(token: str, cam_bytes: bytes) -> None:
    with _IMAGE_STORE_LOCK:
        entry = _IMAGE_STORE.get(token)
        if not entry:
            return
        entry["gradcam"] = cam_bytes
        entry["exp"] = time.time() + IMAGE_TTL_SECONDS  # (선택) 조회 시 TTL 연장

def _get_image_from_store(token: str, kind: str) -> Optional[bytes]:
    _purge_expired_tokens()
    with _IMAGE_STORE_LOCK:
        entry = _IMAGE_STORE.get(token)
        if not entry:
            return None
        # 조회 시 TTL 연장(선택)
        entry["exp"] = time.time() + IMAGE_TTL_SECONDS
        if kind == "orig":
            return entry.get("orig")
        elif kind in ("gradcam", "cam"):
            return entry.get("gradcam")
        return None

# ===== 유틸: 리사이즈 & 직렬화 =====
def _downscale_pil(img: Image.Image, max_side: int) -> Image.Image:
    w, h = img.size
    m = max(w, h)
    if m <= max_side:
        return img
    scale = max_side / float(m)
    new_w = max(1, int(w * scale))
    new_h = max(1, int(h * scale))
    return img.resize((new_w, new_h), Image.LANCZOS)

def _pil_to_png_bytes(img_pil: Image.Image) -> bytes:
    buf = io.BytesIO()
    img_pil.save(buf, format="PNG", optimize=True)
    return buf.getvalue()

# ===== CAM 온디맨드 생성 (요청 시에만 메모리 사용) =====
def _generate_cam_on_demand(token: str) -> Optional[bytes]:
    """
    orig가 캐시에 있을 때만 임시파일 경유로 Grad-CAM 생성 → 캐시에 저장 후 반환.
    DISABLE_CAM=1 이어도 /image?kind=gradcam 요청 시 호출되어 생성한다.
    - CAM 계산은 CAM_MAX_DIM으로 더 작게 수행
    - UI 정합성을 위해 최종 이미지는 orig와 동일 크기로 리사이즈
    """
    orig_bytes = _get_image_from_store(token, "orig")
    if not orig_bytes:
        return None

    # 원본 크기 기억
    try:
        orig_pil = Image.open(io.BytesIO(orig_bytes)).convert("RGB")
        orig_w, orig_h = orig_pil.size
    except Exception:
        return None

    # CAM 계산용 다운스케일
    cam_in = _downscale_pil(orig_pil, CAM_MAX_DIM)

    tmp_path = None
    try:
        # 임시 PNG 저장 (Freq_CAM_init이 파일 경로 필요)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name
        buf = io.BytesIO()
        cam_in.save(buf, format="PNG", optimize=True)
        with open(tmp_path, "wb") as f:
            f.write(buf.getvalue())

        # CAM 생성
        cam_arr = Freq_CAM_init(image_save_path=tmp_path, model_path=MODEL_PATH)
        cam_img = cam_arr if isinstance(cam_arr, Image.Image) else Image.fromarray(np.asarray(cam_arr))

        # 최종 반환은 원본 크기에 맞춰 리사이즈 (UI 정합성)
        if cam_img.size != (orig_w, orig_h):
            cam_img = cam_img.resize((orig_w, orig_h), Image.BILINEAR)

        cam_png = _pil_to_png_bytes(cam_img)
        _update_cam_in_store(token, cam_png)
        return cam_png
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass

# ===== 코어: 디스크 영구 저장 없이 추론 수행 =====
async def _predict_deepfake_freqnet_no_persist(upload_file: UploadFile) -> Tuple[float, bool, bytes, Optional[bytes]]:
    """
    - 업로드 이미지를 메모리에서 PNG 정규화(+다운스케일: MAX_IMG_DIM)
    - Windows 호환 임시파일 경유로 모델 추론
    - (옵션) Grad-CAM 사전 생성(DISABLE_CAM=0일 때만; CAM_MAX_DIM으로 줄여 계산)
    - 원본/Grad-CAM PNG 바이트 반환
    """
    # 업로드 읽기
    raw = await upload_file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="빈 파일입니다.")

    # 원본을 PIL로 파싱 (유효성 체크 겸 RGB 변환) + 저메모리 다운스케일
    try:
        orig_img = Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=415, detail="유효한 이미지 파일이 아닙니다.")
    orig_img = _downscale_pil(orig_img, MAX_IMG_DIM)

    # 메모리에서 PNG 바이트로 정규화
    orig_png = _pil_to_png_bytes(orig_img)

    tmp_path = None
    try:
        # Windows: NamedTemporaryFile(delete=False) 후 수동 삭제
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name
        with open(tmp_path, "wb") as f:
            f.write(orig_png)

        # ---- 모델 추론 (기존 함수가 image_path를 받으므로 임시 경로 사용) ----
        prediction, result = run_freqnet_detection(
            model_path=MODEL_PATH,
            image_path=tmp_path,
            cuda=torch.cuda.is_available()
        )
        # result: [real_score, fake_score] 가정
        fake_confidence: float = float(result[1]) if isinstance(result, (list, tuple, np.ndarray)) and len(result) > 1 else float(result)
        is_fake: bool = (int(prediction) == 1)

        # ---- Grad-CAM (사전 생성: DISABLE_CAM=0일 때만; CAM_MAX_DIM으로 축소 계산) ----
        cam_png: Optional[bytes] = None
        if not DISABLE_CAM:
            # CAM 입력용으로 더 작은 PNG를 임시 경로에 기록
            cam_pil = _downscale_pil(orig_img, CAM_MAX_DIM)
            with open(tmp_path, "wb") as f:
                f.write(_pil_to_png_bytes(cam_pil))

            cam_arr = Freq_CAM_init(image_save_path=tmp_path, model_path=MODEL_PATH)
            cam_img = cam_arr if isinstance(cam_arr, Image.Image) else Image.fromarray(np.asarray(cam_arr))

            # 최종 이미지는 원본(=orig_img) 크기에 맞춤
            if cam_img.size != orig_img.size:
                cam_img = cam_img.resize(orig_img.size, Image.BILINEAR)

            cam_png = _pil_to_png_bytes(cam_img)

        return fake_confidence, is_fake, orig_png, cam_png

    finally:
        # 임시파일 제거 (영구 저장 방지)
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass

# ===== 라우팅 =====

@router.post("/create", status_code=201)
def create_detection_session_endpoint(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """새로운 탐지 세션 생성"""
    session = detection_service.create_detection_session(db=db, user_id=user.id)
    return {"detectionId": session.id}

@router.post("/{detectionId}/run", response_model=DetectionRunResponse, status_code=202)
async def run_detection(
    detectionId: str,
    image: UploadFile = File(None),
    file: UploadFile = File(None),  # 프런트가 'file' 필드명을 쓰는 경우 호환
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    탐지 수행 (디스크 미저장) 및 결과 저장
    - 원본/Grad-CAM 이미지는 메모리 캐시에 TTL로 보관
    - DB details에는 token만 기록 (파일명 저장 안 함)
    """
    # 세션 확인
    session = detection_service.get_detection_session(db, detectionId, user.id)
    if not session:
        raise HTTPException(status_code=404, detail="탐지 세션을 찾을 수 없습니다.")
    if getattr(session, "status", None) == "completed":
        raise HTTPException(status_code=409, detail="이미 탐지가 완료된 세션입니다.")

    upload = image or file
    if not upload:
        raise HTTPException(status_code=400, detail="이미지 파일이 필요합니다. (form field: image)")

    try:
        fake_confidence, is_fake, orig_png, cam_png = await _predict_deepfake_freqnet_no_persist(upload)
    except HTTPException:
        raise
    except Exception as e:
        # 내부 예외는 500으로 래핑
        print(f"[run_detection] error for {detectionId}: {e}")
        raise HTTPException(status_code=500, detail="탐지 처리 중 오류가 발생했습니다.")

    # 메모리 캐시에 저장하고 토큰 발급
    token = _put_images_to_store(orig_png, cam_png)

    # DB에 token 저장
    details = f"token={token}"
    detection_service.create_detection_result(
        db=db,
        session_id=session.id,
        is_deepfake=is_fake,
        confidence=fake_confidence,
        details=details
    )
    detection_service.mark_session_completed(db, session)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    # 응답
    return DetectionRunResponse(
        detectionId=session.id,
        message="탐지 요청이 정상적으로 접수되었습니다.",
        estimatedTime=0
    )

@router.get("/result/{detectionId}", response_model=DetectionResultResponse)
def get_detection_result(
    detectionId: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    탐지 결과 + 이미지 URL 반환
    - details에 token=xxxx 저장 → 동적 이미지 엔드포인트 URL 생성
    - 온디맨드 전략: CAM 사전 생성 여부와 무관하게 gradcamUrl을 항상 내려준다.
      프런트가 해당 URL을 호출하면 /image에서 즉석 생성(_generate_cam_on_demand)한다.
    """
    session = detection_service.get_detection_session(db, detectionId, user.id)
    if not session:
        raise HTTPException(status_code=404, detail="탐지 세션을 찾을 수 없습니다.")

    result = detection_service.get_detection_result(db, detectionId)
    if not result:
        # 기존 클라이언트가 폴링을 404 기준으로 구현했다면 유지
        raise HTTPException(status_code=404, detail="탐지 결과를 찾을 수 없습니다.")

    token = None
    if result.details:
        m = re.search(r"token=([a-f0-9]+)", result.details)
        token = m.group(1) if m else None

    image_url = f"/detections/image?kind=orig&t={token}" if token else None
    gradcam_url = f"/detections/image?kind=gradcam&t={token}" if token else None

    return DetectionResultResponse(
        detectionId=session.id if hasattr(session, "id") else detectionId,
        result=DetectionResultData(
            isDeepfake=bool(result.is_deepfake),
            confidence=float(result.confidence),
            imageUrl=image_url,
            gradcamUrl=gradcam_url,
            details=result.details
        )
    )

@router.get("/image")
def get_image(kind: str, t: str):
    """
    메모리에 있는 PNG 이미지를 스트리밍 반환.
    - kind=gradcam인데 캐시에 없으면 그때 즉시 생성(온디맨드)
    - 디스크 고정 저장 없음
    """
    if kind not in ("orig", "gradcam"):
        raise HTTPException(status_code=400, detail="kind must be 'orig' or 'gradcam'")

    data = _get_image_from_store(t, kind)

    # 🔽 온디맨드 CAM 생성: 필요할 때만 만든다
    if kind in ("gradcam", "cam") and not data:
        data = _generate_cam_on_demand(t)

    if not data:
        # TTL 만료/토큰 없음 → 404
        raise HTTPException(status_code=404, detail="이미지가 만료되었거나 토큰이 유효하지 않습니다.")

    return StreamingResponse(
        io.BytesIO(data),
        media_type="image/png",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
            "Content-Disposition": f'inline; filename="{kind}.png"',
        },
    )
