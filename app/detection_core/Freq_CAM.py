# import torch
# import torch.nn.functional as F
# import numpy as np
# import cv2
# from matplotlib import pyplot as plt
# from PIL import Image
# import torchvision.transforms as transforms
# from freqnet import freqnet

# class GradCAM:
#     def __init__(self, model, target_layer):
#         self.model = model
#         self.target_layer = target_layer
#         self.gradients = None
#         self.activations = None

#         # Register hooks to capture gradients and activations
#         target_layer.register_forward_hook(self.save_activation)
#         target_layer.register_backward_hook(self.save_gradient)

#     def save_activation(self, module, input, output):
#         self.activations = output

#     def save_gradient(self, module, grad_input, grad_output):
#         self.gradients = grad_output[0]

#     def __call__(self, x, class_idx=None):
#         # Forward pass
#         output = self.model(x)
        
#         # Get the score for the target class
#         if class_idx is None:
#             class_idx = output.argmax(dim=1).item()
        
#         score = output[:, class_idx]
        
#         # Backward pass
#         self.model.zero_grad()
#         score.backward(retain_graph=True)
        
#         # Calculate weights
#         weights = self.gradients.mean(dim=[2, 3], keepdim=True)
        
#         # Calculate GradCAM
#         cam = (weights * self.activations).sum(dim=1, keepdim=True)
#         cam = F.relu(cam)  # Apply ReLU to only focus on positive influences
#         cam = cam.squeeze().detach().cpu().numpy()

#         # Normalize the CAM
#         cam = cv2.resize(cam, (x.size(2), x.size(3)))
#         cam = (cam - cam.min()) / (cam.max() - cam.min())  # Normalize between 0-1
#         return cam
    
# def show_gradcam_on_image(img: np.ndarray, mask: np.ndarray, use_rgb: bool = True, colormap: int = cv2.COLORMAP_JET, image_weight: float = 0.5) -> np.ndarray:
#     """
#     Overlay CAM mask on the image as a heatmap.
#     Args:
#         img (np.ndarray): Base image in RGB format, normalized to [0, 1].
#         mask (np.ndarray): CAM mask, should be a single-channel image with values normalized to [0, 1].
#         use_rgb (bool): Set True if the img is in RGB format, False for BGR.
#         colormap (int): Colormap used for visualizing the heatmap.
#         image_weight (float): Weight of the original image in the blend.

#     Returns:
#         np.ndarray: Image with CAM overlay.
#     """
#     # Convert mask to a heatmap using the specified colormap
#     heatmap = cv2.applyColorMap(np.uint8(255 * mask), colormap)
#     if use_rgb:
#         heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)
#     heatmap = np.float32(heatmap) / 255

#     # Check if the input image is normalized
#     if np.max(img) > 1:
#         raise ValueError("The input image should be np.float32 in the range [0, 1]")

#     # Check image weight
#     if not (0 <= image_weight <= 1):
#         raise ValueError(f"image_weight should be in the range [0, 1]. Got: {image_weight}")

#     # Combine the heatmap with the original image
#     superimposed_img = (1 - image_weight) * heatmap + image_weight * img
#     superimposed_img = superimposed_img / np.max(superimposed_img)  # Normalize to [0, 1]
#     return np.uint8(255 * superimposed_img)
# ## version show_cam_on_image

# def apply_gradcam(gradcam, image, target_class=None):
#     cam = gradcam(image, target_class)
#     rgb_image = np.float32(image.squeeze().permute(1, 2, 0).detach().cpu().numpy())
    
#     # 정규화된 RGB 이미지 검증
#     if rgb_image.max() > 1.0:
#         rgb_image /= 255.0
    
#     cam_image = show_gradcam_on_image(rgb_image, cam, use_rgb=True, colormap=cv2.COLORMAP_JET, image_weight=0.5)
#     return cam_image

# # def apply_gradcam(gradcam, image, target_class=None):
# #     cam = gradcam(image, target_class)
# #     heatmap = cv2.applyColorMap(np.uint8(255 * cam), cv2.COLORMAP_JET)  # 컬러맵 변경
# #     heatmap = np.float32(heatmap) / 255
# #     # 이미지와 열지도 합성 비율 조정
# #     superimposed_img = 0.5 * heatmap + 0.5 * np.float32(image.squeeze().permute(1, 2, 0).detach().cpu().numpy())
# #     superimposed_img = superimposed_img / superimposed_img.max()
# #     return np.uint8(255 * superimposed_img)


# # Load your FreqNet model and set to eval mode
# # model_path = "4-classes-freqnet-v2.pth"
# def Freq_CAM_init(image_save_path, model_path):
#     # model_path = "./algorithms/Grad_FreqNet/mod_train_ver1.pth"
#     model = freqnet(num_classes=1)

#     # Check for CUDA availability and set device
#     device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
#     model.to(device)

#     checkpoint = torch.load(model_path, map_location=device)

#     if 'model' in checkpoint:
#         model.load_state_dict(checkpoint['model'], strict=False)
#     else:
#         model.load_state_dict(checkpoint, strict=False)

#     model.eval()
#     # for name, module in model.named_modules():
#     #     print(name, module)

#     # Choose the target layer for GradCAM, e.g., layer2 in FreqNet
#     target_layer = model.layer2[3].conv3
#     gradcam = GradCAM(model, target_layer)

#     # Load and preprocess an input image
#     # image_path = "AMI_facedancer.png"  # 이미지 경로 지정
#     image_path = image_save_path
#     # image_path = "182644_6.png"
#     img = Image.open(image_path).convert('RGB')
#     transform = transforms.Compose([
#         transforms.Resize((224, 224)),  # 모델 입력 크기에 맞게 조정
#         transforms.ToTensor(),
#     ])

#     image = transform(img).unsqueeze(0).to(device)  # (1, 3, H, W) 형태로 변환 후 장치로 이동
#     image.requires_grad = True  # GradCAM 계산을 위해 gradients가 필요함

#     # Apply GradCAM
#     target_class = 0  # Specify the target class if necessary
#     cam_image = apply_gradcam(gradcam, image, target_class)
#     return cam_image
#     # Display the result
#     # plt.imshow(cam_image)
#     # plt.axis('off')
#     # plt.show()

# app/detection_core/Freq_CAM.py
# 경량 Grad-CAM 구현:
# - 모델 싱글톤 재사용(매 호출 로드 금지) : inference.get_model()
# - 타깃 conv 레이어 1회 탐색 후 캐시
# - torchvision / opencv 미사용(PIL+NumPy로 전처리/오버레이)
# - 입력 224 고정, Grad-CAM 계산 시에만 enable_grad
# - 반환: PIL.Image(Image.Image) (필요 시 호출측에서 PNG 인코딩)

# app/detection_core/Freq_CAM.py
from __future__ import annotations

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from typing import Tuple
import weakref

from .inference import get_model  # 싱글톤 모델/디바이스 재사용


# ---- 모델별 타깃 레이어 캐시(모델 인스턴스 키 기반) ----
_TARGET_LAYER_CACHE: "weakref.WeakKeyDictionary[torch.nn.Module, torch.nn.Module]" = weakref.WeakKeyDictionary()


def _get_target_layer(model: torch.nn.Module) -> torch.nn.Module:
    """
    모델에서 Grad-CAM용 타깃 레이어(마지막 Conv2d)를 찾아 캐시.
    """
    if model in _TARGET_LAYER_CACHE:
        return _TARGET_LAYER_CACHE[model]

    target = None
    for m in reversed(list(model.modules())):
        if isinstance(m, torch.nn.Conv2d):
            target = m
            break
    if target is None:
        raise RuntimeError("Could not find a convolutional layer for Grad-CAM.")

    _TARGET_LAYER_CACHE[model] = target
    return target


class GradCAM:
    """
    경량 Grad-CAM 구현 (full backward hook 사용).
    - target_layer 활성맵/그라디언트만 캡처
    - 파라미터 grad는 불필요
    """
    def __init__(self, model: torch.nn.Module, target_layer: torch.nn.Module):
        self.model = model
        self.target_layer = target_layer
        self._act = None
        self._grad = None

        self._hf = target_layer.register_forward_hook(self._on_fwd)
        # PyTorch 버전에 따라 full_backward_hook이 없을 수 있어 폴백 지원
        if hasattr(target_layer, "register_full_backward_hook"):
            self._hb = target_layer.register_full_backward_hook(self._on_bwd)  # type: ignore[attr-defined]
        else:
            self._hb = target_layer.register_backward_hook(self._on_bwd)       # deprecated fallback

    def _on_fwd(self, module, inputs, output):
        self._act = output  # [N,C,H,W]

    def _on_bwd(self, module, grad_input, grad_output):
        self._grad = grad_output[0]  # dScore/dActivation

    def remove_hooks(self):
        for h in (self._hf, self._hb):
            try:
                h.remove()
            except Exception:
                pass

    @torch.inference_mode(False)
    def __call__(self, x: torch.Tensor, class_idx: int | None = None) -> torch.Tensor:
        """
        x: [1,3,H,W], requires_grad=True 권장
        return: [H,W] float32, 0..1
        """
        logits = self.model(x)  # [1,1] or [1,K]
        if class_idx is None:
            if logits.ndim == 2 and logits.size(1) > 1:
                class_idx = int(torch.argmax(logits, dim=1).item())
            else:
                class_idx = 0

        score = logits[0, class_idx] if logits.ndim == 2 else logits[0, 0]
        self.model.zero_grad(set_to_none=True)
        score.backward(retain_graph=False)

        A = self._act
        dA = self._grad
        if A is None or dA is None:
            raise RuntimeError("GradCAM hooks did not capture activation/gradient.")

        w = dA.mean(dim=(2, 3), keepdim=True)      # [1,C,1,1]
        cam = torch.relu((w * A).sum(dim=1))       # [1,H,W]
        cam = cam.squeeze(0)                        # [H,W]
        cam = (cam - cam.min()) / (cam.max() - cam.min() + 1e-6)
        return cam  # [H,W], float32 (0..1)


# ---- 전처리/시각화: torchvision/cv2 없이 PIL+NumPy ----
_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
_STD  = np.array([0.229, 0.224, 0.225], dtype=np.float32)


def _preprocess_for_model(pil: Image.Image, size: int = 224) -> torch.Tensor:
    img = pil.convert("RGB").resize((size, size), Image.BILINEAR)
    arr = np.asarray(img, dtype=np.float32) / 255.0
    arr = (arr - _MEAN) / _STD
    t = torch.from_numpy(arr).permute(2, 0, 1).unsqueeze(0)  # [1,3,H,W]
    return t


def _preprocess_for_vis(pil: Image.Image, size: int = 224) -> np.ndarray:
    img = pil.convert("RGB").resize((size, size), Image.BILINEAR)
    arr = np.asarray(img, dtype=np.float32) / 255.0  # [H,W,3] 0..1
    return arr


def _overlay_pil(base_rgb01: np.ndarray, cam01: torch.Tensor, alpha: float = 0.5) -> Image.Image:
    """
    base_rgb01: [H,W,3] float32(0..1)
    cam01:      [h,w]   torch.float32(0..1) — 필요 시 bilinear로 resize
    return:     PIL.Image (RGB)
    """
    H, W, _ = base_rgb01.shape
    if cam01.shape != (H, W):
        cam01 = F.interpolate(cam01.unsqueeze(0).unsqueeze(0), size=(H, W),
                              mode="bilinear", align_corners=False).squeeze()

    cam_u8 = (cam01.clamp(0, 1).mul(255).byte().cpu().numpy())  # [H,W]
    heat = Image.fromarray(cam_u8, mode="L")

    base = Image.fromarray(np.clip(base_rgb01 * 255.0, 0, 255).astype(np.uint8), mode="RGB").convert("RGBA")
    red = Image.new("RGBA", (W, H), (255, 0, 0, 0))
    red.putalpha(heat)  # CAM 강도를 알파로

    out = Image.alpha_composite(base, red)
    if alpha != 1.0:
        a = out.split()[-1].point(lambda p: int(p * alpha))
        out.putalpha(a)

    return out.convert("RGB")


# ==== 공개 API ===============================================================

def Freq_CAM_init(image_save_path: str, model_path: str, target_class: int | None = 0) -> Image.Image:
    """
    파일 경로의 이미지를 읽어 Grad-CAM 오버레이 결과(PIL.Image)를 반환.
    - 모델은 inference.get_model() 싱글톤 재사용(메모리 절약)
    - 타깃 레이어는 1회 탐색 후 모델별 캐시
    - 입력/시각화는 224x224 고정(경량)
    """
    # 1) 모델 & 디바이스
    model, device = get_model(model_path, cuda=torch.cuda.is_available())
    model.eval()  # 안전 차원

    # 2) 이미지 로딩/전처리
    pil = Image.open(image_save_path).convert("RGB")
    x_model = _preprocess_for_model(pil, size=224).to(device)   # [1,3,224,224]
    x_vis01 = _preprocess_for_vis(pil, size=224)                # [224,224,3] 0..1

    # 3) Grad-CAM 실행 (이 블록에서만 grad 허용)
    target_layer = _get_target_layer(model)
    cammer = GradCAM(model, target_layer)
    try:
        x_model.requires_grad_(True)
        with torch.enable_grad():
            cam01 = cammer(x_model, class_idx=target_class)     # [h,w] float32 0..1
    finally:
        cammer.remove_hooks()

    # 4) 오버레이(메모리 절약: PIL 합성)
    out_img = _overlay_pil(x_vis01, cam01, alpha=0.5)           # PIL.Image
    return out_img
