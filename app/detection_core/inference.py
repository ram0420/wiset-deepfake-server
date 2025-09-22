# import torch
# import os
# import numpy as np
# import time
# from PIL import Image
# import torchvision.transforms as transforms
# from .freqnet import freqnet  


# # 이미지 로드 및 전처리 함수
# def load_image(image_path, no_resize=False, no_crop=True):
#     """
#     이미지를 로드하고 전처리하는 함수
#     image_path: 이미지 경로
#     no_resize: 이미지 리사이징 여부
#     no_crop: 이미지 크롭 여부
#     """
#     img = Image.open(image_path).convert('RGB')

#     preprocess = []
#     if not no_resize:
#         preprocess.append(transforms.Resize((256, 256)))  # 원하는 크기로 조정
#     if not no_crop:
#         preprocess.append(transforms.CenterCrop(224))  # 원하는 크기로 크롭

#     preprocess.extend([
#         transforms.ToTensor(),  # 텐서로 변환
#         transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])  # 이미지넷 정규화
#     ])
    
#     transform = transforms.Compose(preprocess)
#     img_tensor = transform(img)
    
#     return img_tensor

# # 단일 이미지에 대해 FreqNet 모델을 사용하여 예측을 수행하는 함수
# def run_freqnet_detection(model_path, image_path, cuda=True):
#     """
#     FreqNet Detection을 단일 이미지에 대해 실행하는 함수
#     model_path: 모델의 경로
#     image_path: 평가할 이미지 경로
#     cuda: CUDA 사용 여부
#     """
#     # 모델 로드
#     model = freqnet(num_classes=1)
#     checkpoint = torch.load(model_path, map_location='cpu')
    
#     if 'model' in checkpoint:
#         model.load_state_dict(checkpoint['model'], strict=False)
#     else:
#         model.load_state_dict(checkpoint, strict=False)

#     # CUDA 사용 시 GPU로 이동
#     if cuda and torch.cuda.is_available():
#         model.cuda()
#     model.eval()

#     # 이미지 전처리 및 로드
#     image = load_image(image_path)
#     image = image.unsqueeze(0)  # 배치 차원 추가

#     # 모델 예측
#     with torch.no_grad():
#         if cuda:
#             image = image.cuda()
#         output = model(image)
#         conf = torch.sigmoid(output).item()  # 확률 값으로 변환

#     # 예측 결과
#     prediction = 1 if conf > 0.5 else 0  # 50% 기준으로 Fake 여부
#     result = [1 - conf, conf]  # Real confidence, Fake confidence
#     print("Prediction")
#     print(prediction)
#     print("result")
#     print(result)
#     return prediction, result  # 예측된 레이블(Fake/Real)과 confidence 값 반환

# # 예시 코드
# if __name__ == '__main__':
#     model_path = './DCS_freqnet.pth'  # 모델 경로 설정
#     image_path = './images/input_image.png'  # 이미지 경로 설정
#     cuda = True  # CUDA 사용 여부

#     # 함수 호출
#     prediction, result = run_freqnet_detection(model_path, image_path, cuda)

#     # 결과 출력
#     print(f"Prediction: {'Fake' if prediction == 1 else 'Real'}")
#     print(f"Confidence: Real = {result[0]:.4f}, Fake = {result[1]:.4f}")

# app/detection_core/inference.py
from __future__ import annotations

import io
import threading
from typing import Tuple, List, Optional

import numpy as np
import torch
from PIL import Image, ImageOps

from .freqnet import freqnet


# =====================
# 전역 싱글톤 모델 로딩
#  - model_path/디바이스가 바뀌면 자동 재로딩
# =====================
_MODEL: Optional[torch.nn.Module] = None
_DEVICE: Optional[torch.device] = None
_MODEL_PATH: Optional[str] = None
_LOCK = threading.Lock()


def _safe_extract_state(ckpt):
    """다양한 체크포인트 포맷을 안전하게 처리."""
    if isinstance(ckpt, dict):
        for key in ("model", "state_dict", "weights"):
            if key in ckpt:
                return ckpt[key]
    return ckpt


def _load_model(model_path: str, device: torch.device) -> torch.nn.Module:
    model = freqnet(num_classes=1)

    # PyTorch 2.x면 weights_only=True로 불필요한 객체 역직렬화 방지
    try:
        ckpt = torch.load(model_path, map_location="cpu", weights_only=True)  # type: ignore[arg-type]
    except TypeError:
        ckpt = torch.load(model_path, map_location="cpu")

    state = _safe_extract_state(ckpt)
    if isinstance(state, dict):
        model.load_state_dict(state, strict=False)
    else:
        # 이례적으로 nn.Module 형태가 오면 그대로 복사(거의 없음)
        model.load_state_dict(state.state_dict(), strict=False)

    # 추론 전용 설정(파라미터 grad off) — Grad-CAM엔 영향 없음
    for p in model.parameters():
        p.requires_grad_(False)

    model.to(device).eval()
    return model


def get_model(model_path: str, cuda: bool = True) -> Tuple[torch.nn.Module, torch.device]:
    """
    싱글톤 모델과 디바이스 반환.
    - model_path 또는 디바이스가 바뀌면 재로딩
    """
    global _MODEL, _DEVICE, _MODEL_PATH
    want_device = torch.device("cuda" if cuda and torch.cuda.is_available() else "cpu")
    with _LOCK:
        if _MODEL is None or _DEVICE != want_device or _MODEL_PATH != model_path:
            _MODEL = _load_model(model_path, want_device)
            _DEVICE = want_device
            _MODEL_PATH = model_path
    return _MODEL, _DEVICE  # type: ignore[return-value]


# =====================
# 전처리 (PIL+NumPy) — torchvision 미사용
# =====================
_IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
_IMAGENET_STD  = np.array([0.229, 0.224, 0.225], dtype=np.float32)


def _preprocess_pil(img_pil: Image.Image,
                    no_resize: bool = False,
                    no_crop: bool = True,
                    resize_to: int = 256,
                    crop_to: int = 224) -> torch.Tensor:
    """
    PIL.Image -> torch.FloatTensor [C,H,W], ImageNet 정규화.
    - 기본: 256 리사이즈 후 224 중앙 크롭(관례)
    - 경량화를 위해 필요 시 no_resize/no_crop 설정 가능
    """
    img = img_pil.convert("RGB")
    if not no_resize and resize_to:
        img = img.resize((resize_to, resize_to), Image.BILINEAR)
    if not no_crop and crop_to and (img.size[0] != crop_to or img.size[1] != crop_to):
        img = ImageOps.fit(img, (crop_to, crop_to), method=Image.BILINEAR, centering=(0.5, 0.5))

    arr = np.asarray(img, dtype=np.float32) / 255.0          # [H,W,3] in 0..1
    arr = (arr - _IMAGENET_MEAN) / _IMAGENET_STD             # 정규화
    t = torch.from_numpy(arr).permute(2, 0, 1)               # [3,H,W]
    return t


# =====================
# 기존 API(경로 입력) - 호환 유지
# =====================
def load_image(image_path: str,
               no_resize: bool = False,
               no_crop: bool = True) -> torch.Tensor:
    img = Image.open(image_path).convert("RGB")
    return _preprocess_pil(img, no_resize=no_resize, no_crop=no_crop)


def run_freqnet_detection(model_path: str,
                          image_path: str,
                          cuda: bool = True) -> Tuple[int, List[float]]:
    """
    파일 경로 입력으로 분류 수행.
    반환: (pred, [real_conf, fake_conf])
    """
    model, device = get_model(model_path, cuda=cuda)
    image = load_image(image_path).unsqueeze(0).to(device)  # [1,3,H,W]

    with torch.inference_mode():
        out = model(image)                                  # [1,1] or [1,K]
        if out.ndim == 2 and out.size(1) == 1:
            conf_fake = torch.sigmoid(out).flatten().item()
        else:
            probs = torch.softmax(out, dim=1)[0]
            conf_fake = float(probs[1].item()) if probs.numel() > 1 else float(probs[0].item())

    pred = 1 if conf_fake > 0.5 else 0
    return pred, [1.0 - conf_fake, conf_fake]


# =====================
# 새 API(바이트/메모리 입력)
# =====================
def run_freqnet_detection_from_pil(model_path: str,
                                   img_pil: Image.Image,
                                   cuda: bool = True,
                                   no_resize: bool = False,
                                   no_crop: bool = True) -> Tuple[int, List[float]]:
    model, device = get_model(model_path, cuda=cuda)
    image = _preprocess_pil(img_pil, no_resize=no_resize, no_crop=no_crop).unsqueeze(0).to(device)

    with torch.inference_mode():
        out = model(image)
        if out.ndim == 2 and out.size(1) == 1:
            conf_fake = torch.sigmoid(out).flatten().item()
        else:
            probs = torch.softmax(out, dim=1)[0]
            conf_fake = float(probs[1].item()) if probs.numel() > 1 else float(probs[0].item())

    pred = 1 if conf_fake > 0.5 else 0
    return pred, [1.0 - conf_fake, conf_fake]


def run_freqnet_detection_from_bytes(model_path: str,
                                     img_bytes: bytes,
                                     cuda: bool = True,
                                     no_resize: bool = False,
                                     no_crop: bool = True) -> Tuple[int, List[float]]:
    img_pil = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    return run_freqnet_detection_from_pil(
        model_path,
        img_pil,
        cuda=cuda,
        no_resize=no_resize,
        no_crop=no_crop,
    )
