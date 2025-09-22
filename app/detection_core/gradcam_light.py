# app/routers/detection.py  (핵심 아이디어만, 네 기존 핸들러에 합치면 됨)
from fastapi import APIRouter, UploadFile, HTTPException
from fastapi.responses import FileResponse, Response
from app.detection_core.runtime import startup
from app.detection_core.gradcam_light import GradCAMLight, preprocess_pil, overlay_png
from PIL import Image
import os, asyncio, gc, tempfile

router = APIRouter()
_CAM_LOCK = asyncio.Semaphore(1)   # 동시 1개 실행 (메모리 피크 방지)
CKPT = "app/detection_core/freqnet_finetuned.pth"
runtime = startup(CKPT)

def _atomic_write(data: bytes, final_path: str):
    tmp = final_path + ".tmp"
    with open(tmp, "wb") as f:
        f.write(data); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, final_path)

@router.get("/detections/image")
async def get_image(kind: str, t: str, size: int = 224):
    # kind=orig/gradcam
    if kind == "orig":
        path = f"app/static/uploads/{t}.png"
        if not os.path.exists(path):
            raise HTTPException(404, "orig-not-found")
        return FileResponse(path, media_type="image/png", headers={"Cache-Control":"no-store"})

    if kind == "gradcam":
        cam_path = f"app/static/uploads/{t}_cam.png"
        if os.path.exists(cam_path):
            return FileResponse(cam_path, media_type="image/png", headers={"Cache-Control":"no-store"})

        # 없으면 지금 생성 (동시성 1개)
        async with _CAM_LOCK:
            if os.path.exists(cam_path):  # double-check
                return FileResponse(cam_path, media_type="image/png")

            img_path = f"app/static/uploads/{t}.png"
            if not os.path.exists(img_path):
                raise HTTPException(404, "orig-not-found")

            img = Image.open(img_path)
            x = preprocess_pil(img, size=size)

            # target layer: 평균풀링 직전의 마지막 conv (freqnet 내부 명칭에 맞춰 지정)
            # 예: target = runtime.model.layer2[-1].conv3  등 실제 모듈 경로에 맞게 선택
            target_layer = next(
                m for n,m in runtime.model.named_modules() if isinstance(m, torch.nn.Conv2d)
            )  # 👉 실제로는 "마지막 Conv" 지정 로직으로 바꿔라

            with GradCAMLight(runtime.model, target_layer) as cammer:
                cam = cammer(x, target_class=None)

            png = overlay_png(img, cam, alpha=0.45)
            _atomic_write(png, cam_path)
            del img, x, cam, png
            gc.collect()
            return FileResponse(cam_path, media_type="image/png")

    raise HTTPException(400, "invalid-kind")
