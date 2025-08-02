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
    def __init__(self, model, target_layer):
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None

        # Register hooks to capture gradients and activations
        target_layer.register_forward_hook(self.save_activation)
        target_layer.register_backward_hook(self.save_gradient)

    def save_activation(self, module, input, output):
        self.activations = output

    def save_gradient(self, module, grad_input, grad_output):
        self.gradients = grad_output[0]

    def __call__(self, x, class_idx=None):
        # Forward pass
        output = self.model(x)

        # Get the score for the target class
        if class_idx is None:
            class_idx = output.argmax(dim=1).item()

        score = output[:, class_idx]

        # Backward pass
        self.model.zero_grad()
        score.backward(retain_graph=True)

        # Calculate weights
        weights = self.gradients.mean(dim=[2, 3], keepdim=True)

        # Calculate GradCAM
        cam = (weights * self.activations).sum(dim=1, keepdim=True)
        cam = F.relu(cam)  # Apply ReLU to only focus on positive influences
        cam = cam.squeeze().detach().cpu().numpy()

        # Normalize the CAM
        cam = cv2.resize(cam, (x.size(2), x.size(3)))
        cam = (cam - cam.min()) / (cam.max() - cam.min())
        return cam


def show_gradcam_on_image(img: np.ndarray, mask: np.ndarray, use_rgb: bool = True, colormap: int = cv2.COLORMAP_JET, image_weight: float = 0.5) -> np.ndarray:
    """
    Overlay CAM mask on the image as a heatmap.
    """
    heatmap = cv2.applyColorMap(np.uint8(255 * mask), colormap)
    if use_rgb:
        heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)
    heatmap = np.float32(heatmap) / 255

    if np.max(img) > 1:
        raise ValueError("The input image should be np.float32 in the range [0, 1]")

    if not (0 <= image_weight <= 1):
        raise ValueError(f"image_weight should be in the range [0, 1]. Got: {image_weight}")

    superimposed_img = (1 - image_weight) * heatmap + image_weight * img
    superimposed_img = superimposed_img / np.max(superimposed_img)
    return np.uint8(255 * superimposed_img)


def apply_gradcam(gradcam, image, target_class=None):
    cam = gradcam(image, target_class)
    rgb_image = np.float32(image.squeeze().permute(1, 2, 0).detach().cpu().numpy())

    if rgb_image.max() > 1.0:
        rgb_image /= 255.0

    cam_image = show_gradcam_on_image(rgb_image, cam, use_rgb=True, colormap=cv2.COLORMAP_JET, image_weight=0.5)
    return cam_image


def Freq_CAM_init(image_save_path, model_path):
    """
    Load the model and input image, apply Grad-CAM, and return heatmap image.
    """
    model = freqnet(num_classes=1)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    checkpoint = torch.load(model_path, map_location=device)
    if 'model' in checkpoint:
        model.load_state_dict(checkpoint['model'], strict=False)
    else:
        model.load_state_dict(checkpoint, strict=False)
    model.eval()

    # Target layer for Grad-CAM
    target_layer = model.layer2[3].conv3
    gradcam = GradCAM(model, target_layer)

    # Preprocess input image
    img = Image.open(image_save_path).convert('RGB')
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
    ])
    image = transform(img).unsqueeze(0).to(device)
    image.requires_grad = True

    # Apply Grad-CAM
    cam_image = apply_gradcam(gradcam, image, target_class=0)
    return cam_image
