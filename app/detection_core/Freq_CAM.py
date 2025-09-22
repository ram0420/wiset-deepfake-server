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

from __future__ import annotations

import io
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

# ✅ 싱글톤 모델 재사용
#   get_model() 시그니처는 프로젝트에 따라 다를 수 있으므로
#   (model_path, cuda) / (model_path) / () 3가지 모두 시도.
from .inference import get_model  # 상대경로 주의

# ---- 전역 캐시: 마지막 Conv 레이어 ----
_TARGET_LAYER: torch.nn.Module | None = None


def _get_device_from_model(model: torch.nn.Module) -> torch.device:
    try:
        return next(model.parameters()).device
    except StopIteration:
        # 파라미터가 없는 모듈일 일은 거의 없지만, 안전 장치
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def _resolve_model_and_device(model_path: str) -> tuple[torch.nn.Module, torch.device]:
    """
    inference.get_model()의 다양한 시그니처에 대응해서
    (model, device) 형태로 반환한다.
    """
    model = None
    # 1) (model_path, cuda) 시그니처 시도
    try:
        model = get_model(model_path, cuda=torch.cuda.is_available())  # type: ignore[arg-type]
    except TypeError:
        pass
    # 2) (model_path) 시그니처 시도
    if model is None:
        try:
            model = get_model(model_path)  # type: ignore[call-arg]
        except TypeError:
            pass
    # 3) 인자 없는 시그니처 시도
    if model is None:
        model = get_model()  # type: ignore[call-arg]

    # get_model이 (model, device)를 반환할 수도 있으므로 처리
    if isinstance(model, tuple) and len(model) == 2:
        m, dev = model
        return m.eval(), torch.device(dev)
    else:
        dev = _get_device_from_model(model)
        return model.eval(), dev


def _get_target_layer(model: torch.nn.Module) -> torch.nn.Module:
    """
    한 번만 찾아 전역에 캐시. 모델 구조가 바뀌지 않는다는 가정.
    기본적으로 '마지막 Conv2d'를 사용.
    """
    global _TARGET_LAYER
    if _TARGET_LAYER is not None:
        return _TARGET_LAYER

    # 프로젝트에 특화된 경로가 있다면 여기에 우선 시도 (예: model.layer2[3].conv3)
    # try:
    #     _TARGET_LAYER = model.layer2[3].conv3
    #     return _TARGET_LAYER
    # except Exception:
    #     pass

    # 폴백: 마지막 Conv2d를 뒤에서부터 찾아 사용
    for m in reversed(list(model.modules())):
        if isinstance(m, torch.nn.Conv2d):
            _TARGET_LAYER = m
            break
    if _TARGET_LAYER is None:
        raise RuntimeError("Could not find a convolutional layer for Grad-CAM.")
    return _TARGET_LAYER


class GradCAM:
    """
    경량 Grad-CAM 구현.
    - target_layer에 forward/full-backward hook을 걸어 activation/gradient만 보관
    - 모델 전체 파라미터 gradient는 필요 없음(활성맵에 대한 grad만 필요)
    """
    def __init__(self, model: torch.nn.Module, target_layer: torch.nn.Module):
        self.model = model
        self.target_layer = target_layer
        self._act = None
        self._grad = None
        self._hf = target_layer.register_forward_hook(self._on_fwd)
        self._hb = target_layer.register_full_backward_hook(self._on_bwd)

    def _on_fwd(self, module, inputs, output):
        # output: [N, C, H, W]
        self._act = output

    def _on_bwd(self, module, grad_input, grad_output):
        # grad_output[0]: dScore/dActivation
        self._grad = grad_output[0]

    def remove_hooks(self):
        try:
            self._hf.remove()
        except Exception:
            pass
        try:
            self._hb.remove()
        except Exception:
            pass

    @torch.inference_mode(False)
    def __call__(self, x: torch.Tensor, class_idx: int | None = None) -> torch.Tensor:
        """
        x: [1, 3, H, W] (requires_grad=True 권장; 최소한 target_layer 활성맵에 grad 필요)
        return: CAM tensor [H, W] (float32, 0..1)
        """
        logits = self.model(x)  # [1, K] 또는 [1,1]
        if class_idx is None:
            if logits.ndim == 2 and logits.size(1) > 1:
                class_idx = int(torch.argmax(logits, dim=1).item())
            else:
                class_idx = 0

        score = logits[0, class_idx] if logits.ndim == 2 else logits[0, 0]

        # 역전파는 활성맵에 대한 grad만 필요
        self.model.zero_grad(set_to_none=True)
        score.backward()  # dScore/dActivation → self._grad 채워짐

        A = self._act                          # [1, C, H', W']
        dA = self._grad                        # [1, C, H', W']
        if A is None or dA is None:
            raise RuntimeError("GradCAM hooks did not capture activation/gradient.")

        # 채널 가중치: grad의 spatial 평균
        w = dA.mean(dim=(2, 3), keepdim=True)  # [1, C, 1, 1]
        cam = torch.relu((w * A).sum(dim=1, keepdim=True))  # [1,1,H',W']

        # 0..1 정규화
        cam = cam.squeeze(0).squeeze(0)        # [H', W']
        cam = cam - cam.min()
        denom = cam.max().clamp_min(1e-6)
        cam = cam / denom
        return cam  # [H', W'], float32


# ---- 전처리: torchvision 없이 PIL+NumPy로 구현 ----
_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
_STD  = np.array([0.229, 0.224, 0.225], dtype=np.float32)


def _preprocess_for_model(pil: Image.Image, size: int = 224) -> torch.Tensor:
    """
    PIL → [1,3,H,W] float32, ImageNet 정규화
    """
    img = pil.convert("RGB").resize((size, size), Image.BILINEAR)
    arr = np.asarray(img, dtype=np.float32) / 255.0
    arr = (arr - _MEAN) / _STD  # [H,W,3]
    t = torch.from_numpy(arr).permute(2, 0, 1).unsqueeze(0)  # [1,3,H,W]
    return t


def _preprocess_for_vis(pil: Image.Image, size: int = 224) -> np.ndarray:
    """
    PIL → 시각화용 [H,W,3] float32(0..1)
    """
    img = pil.convert("RGB").resize((size, size), Image.BILINEAR)
    arr = np.asarray(img, dtype=np.float32) / 255.0
    return arr  # [H,W,3], 0..1


# ---- OpenCV 없이 PIL로 히트맵 오버레이 ----
def _overlay_pil(base_rgb01: np.ndarray, mask01: torch.Tensor, alpha: float = 0.5) -> Image.Image:
    """
    base_rgb01: [H,W,3] float32(0..1)
    mask01:     [h,w]   torch.float32(0..1) (CAM, 필요 시 내부에서 resize)
    return: PIL.Image (RGBA 합성 후 RGB로 반환)
    """
    H, W, _ = base_rgb01.shape

    # CAM을 입력 크기에 맞게 resize (bilinear)
    if mask01.shape[0] != H or mask01.shape[1] != W:
        cam = F.interpolate(mask01.unsqueeze(0).unsqueeze(0), size=(H, W), mode="bilinear", align_corners=False)
        cam = cam.squeeze(0).squeeze(0).contiguous()
    else:
        cam = mask01.contiguous()

    cam_u8 = (cam.clamp(0, 1).mul_(255).byte().cpu().numpy())  # [H,W] uint8
    heat = Image.fromarray(cam_u8, mode="L")                   # 그레이 알파

    base = Image.fromarray(np.clip(base_rgb01 * 255.0, 0, 255).astype(np.uint8), mode="RGB").convert("RGBA")
    red = Image.new("RGBA", (W, H), (255, 0, 0, 0))
    red.putalpha(heat)  # 알파=CAM 강도

    out = Image.alpha_composite(base, red)  # 빨간 히트맵 오버레이

    # 전체 투명도 조절(원한다면)
    if alpha != 1.0:
        a = out.split()[-1].point(lambda p: int(p * alpha))
        out.putalpha(a)

    return out.convert("RGB")


# ==== 공개 API ===============================================================

def Freq_CAM_init(image_save_path: str, model_path: str, target_class: int | None = 0) -> Image.Image:
    """
    파일 경로의 이미지를 읽어 Grad-CAM 오버레이 결과(PIL.Image) 반환.
    - 모델은 싱글톤 재사용(메모리 절약)
    - CAM 타깃 레이어는 1회 탐색 후 캐시
    - 입력/시각화는 224x224 고정(경량)
    """
    # 1) 모델 & 디바이스
    model, device = _resolve_model_and_device(model_path)
    model.eval()  # 안전 차원

    # 2) 이미지 로딩/전처리
    pil = Image.open(image_save_path).convert("RGB")
    x_model = _preprocess_for_model(pil, size=224).to(device)    # [1,3,224,224]
    x_vis01 = _preprocess_for_vis(pil, size=224)                 # [224,224,3] 0..1

    # 3) Grad-CAM 실행 (해당 블록에서만 grad 허용)
    target_layer = _get_target_layer(model)
    cammer = GradCAM(model, target_layer)
    try:
        # 활성맵에 대한 gradient가 흐르도록 입력에 grad 허용
        x_model.requires_grad_(True)
        with torch.enable_grad():
            cam01 = cammer(x_model, class_idx=target_class)  # [h,w] float32 0..1 (h,w≈7..14)
    finally:
        cammer.remove_hooks()

    # 4) 오버레이(메모리 절약: PIL 합성)
    out_img = _overlay_pil(x_vis01, cam01, alpha=0.5)  # PIL.Image
    return out_img
