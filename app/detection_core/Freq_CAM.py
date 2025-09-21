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


import torch
import torch.nn.functional as F
import numpy as np
import cv2
from PIL import Image
import torchvision.transforms as transforms
from .freqnet import freqnet  # 상대 경로로 freqnet.py에서 import


class GradCAM:
    """
    Simple Grad-CAM with full backward hook (no FutureWarning).
    target_layer: a conv module (e.g., model.layer2[3].conv3)
    """
    def __init__(self, model: torch.nn.Module, target_layer: torch.nn.Module):
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None
        self._handle_f = target_layer.register_forward_hook(self._save_activation)
        # Use full backward hook to avoid deprecation / missing grads
        self._handle_b = target_layer.register_full_backward_hook(self._save_gradient)

    def remove_hooks(self):
        try:
            self._handle_f.remove()
        except Exception:
            pass
        try:
            self._handle_b.remove()
        except Exception:
            pass

    def _save_activation(self, module, input, output):
        # shape: [N, C, H, W]
        self.activations = output

    def _save_gradient(self, module, grad_input, grad_output):
        # grad_output[0] corresponds to dL/d(activation)
        self.gradients = grad_output[0]

    def __call__(self, x: torch.Tensor, class_idx: int | None = None) -> np.ndarray:
        """
        x: normalized input tensor [N=1, C, H, W] with grad enabled on the graph
        returns: CAM mask as np.float32 in [0,1] with size of input spatial dims
        """
        # Forward
        output = self.model(x)  # shape [1, K] or [1,1]
        if class_idx is None:
            # If binary (1 logit), default to index 0
            if output.shape[1] == 1:
                class_idx = 0
            else:
                class_idx = int(output.argmax(dim=1).item())

        # Score selection
        score = output[:, class_idx]

        # Backward
        self.model.zero_grad(set_to_none=True)
        score.backward(retain_graph=True)

        # Compute weights: global-average-pooling on gradients
        # gradients: [1, C, H, W] -> mean over H,W -> [1, C, 1, 1]
        weights = self.gradients.mean(dim=(2, 3), keepdim=True)

        # CAM: weighted sum of activations
        cam = (weights * self.activations).sum(dim=1, keepdim=True)  # [1,1,H,W]
        cam = F.relu(cam)  # keep positive influences
        cam = cam.squeeze().detach().cpu().float().numpy()  # [H, W]

        # Normalize to [0,1] safely
        cam_min, cam_max = cam.min(), cam.max()
        if cam_max > cam_min:
            cam = (cam - cam_min) / (cam_max - cam_min)
        else:
            cam = np.zeros_like(cam, dtype=np.float32)

        # Resize to match input spatial size
        H, W = x.shape[-2], x.shape[-1]
        cam = cv2.resize(cam, (W, H), interpolation=cv2.INTER_LINEAR)
        return cam


def _overlay_heatmap_on_image(img01: np.ndarray, mask01: np.ndarray,
                              use_rgb: bool = True,
                              colormap: int = cv2.COLORMAP_JET,
                              image_weight: float = 0.5) -> np.ndarray:
    """
    img01: float32 in [0,1], shape [H,W,3]
    mask01: float32 in [0,1], shape [H,W]
    return: uint8 RGB image
    """
    heatmap = cv2.applyColorMap(np.uint8(255 * mask01), colormap)
    if use_rgb:
        heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)
    heatmap = heatmap.astype(np.float32) / 255.0

    img01 = np.clip(img01.astype(np.float32), 0.0, 1.0)
    alpha = float(np.clip(image_weight, 0.0, 1.0))

    blended = (1.0 - alpha) * heatmap + alpha * img01
    m = blended.max()
    if m > 0:
        blended /= m
    return np.uint8(255 * blended)


def Freq_CAM_init(image_save_path: str, model_path: str, target_class: int | None = 0) -> np.ndarray:
    """
    Load the model and input image, apply Grad-CAM, and return heatmap image (RGB uint8 ndarray).
    - Uses full backward hook (no deprecation warning)
    - Uses normalized input for model, and unnormalized for visualization overlay
    """
    # ---- Device & model ----
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = freqnet(num_classes=1).to(device).eval()

    # Load weights
    ckpt = torch.load(model_path, map_location=device)
    state = ckpt["model"] if isinstance(ckpt, dict) and "model" in ckpt else ckpt
    model.load_state_dict(state, strict=False)

    # ---- Pick target layer (fallback-safe) ----
    # Default path from your code; if it fails, try to find the last conv
    try:
        target_layer = model.layer2[3].conv3
    except Exception:
        # Fallback: best-effort to get a last conv-like module
        target_layer = None
        for m in reversed(list(model.modules())):
            if isinstance(m, torch.nn.Conv2d):
                target_layer = m
                break
        if target_layer is None:
            raise RuntimeError("Could not find a convolutional layer for Grad-CAM.")

    gradcam = GradCAM(model, target_layer)

    # ---- Preprocess (two branches) ----
    # For model input (normalized like inference.py):
    tf_model = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225]),
    ])
    # For visualization overlay (0..1 range):
    tf_vis = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),  # 0..1
    ])

    pil = Image.open(image_save_path).convert("RGB")
    x_model = tf_model(pil).unsqueeze(0).to(device)
    x_model.requires_grad_(True)  # need gradients for CAM
    x_vis = tf_vis(pil).permute(1, 2, 0).cpu().numpy().astype(np.float32)  # [H,W,3] in 0..1

    # ---- Compute CAM ----
    with torch.enable_grad():  # ensure grads are enabled here
        cam = gradcam(x_model, class_idx=target_class)

    gradcam.remove_hooks()

    # ---- Overlay & return ----
    cam_rgb = _overlay_heatmap_on_image(x_vis, cam, use_rgb=True,
                                        colormap=cv2.COLORMAP_JET,
                                        image_weight=0.5)
    return cam_rgb
