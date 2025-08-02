import torch
import os
import numpy as np
import time
from PIL import Image
import torchvision.transforms as transforms
from .freqnet import freqnet  


# 이미지 로드 및 전처리 함수
def load_image(image_path, no_resize=False, no_crop=True):
    """
    이미지를 로드하고 전처리하는 함수
    image_path: 이미지 경로
    no_resize: 이미지 리사이징 여부
    no_crop: 이미지 크롭 여부
    """
    img = Image.open(image_path).convert('RGB')

    preprocess = []
    if not no_resize:
        preprocess.append(transforms.Resize((256, 256)))  # 원하는 크기로 조정
    if not no_crop:
        preprocess.append(transforms.CenterCrop(224))  # 원하는 크기로 크롭

    preprocess.extend([
        transforms.ToTensor(),  # 텐서로 변환
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])  # 이미지넷 정규화
    ])
    
    transform = transforms.Compose(preprocess)
    img_tensor = transform(img)
    
    return img_tensor

# 단일 이미지에 대해 FreqNet 모델을 사용하여 예측을 수행하는 함수
def run_freqnet_detection(model_path, image_path, cuda=True):
    """
    FreqNet Detection을 단일 이미지에 대해 실행하는 함수
    model_path: 모델의 경로
    image_path: 평가할 이미지 경로
    cuda: CUDA 사용 여부
    """
    # 모델 로드
    model = freqnet(num_classes=1)
    checkpoint = torch.load(model_path, map_location='cpu')
    
    if 'model' in checkpoint:
        model.load_state_dict(checkpoint['model'], strict=False)
    else:
        model.load_state_dict(checkpoint, strict=False)

    # CUDA 사용 시 GPU로 이동
    if cuda and torch.cuda.is_available():
        model.cuda()
    model.eval()

    # 이미지 전처리 및 로드
    image = load_image(image_path)
    image = image.unsqueeze(0)  # 배치 차원 추가

    # 모델 예측
    with torch.no_grad():
        if cuda:
            image = image.cuda()
        output = model(image)
        conf = torch.sigmoid(output).item()  # 확률 값으로 변환

    # 예측 결과
    prediction = 1 if conf > 0.5 else 0  # 50% 기준으로 Fake 여부
    result = [1 - conf, conf]  # Real confidence, Fake confidence
    print("Prediction")
    print(prediction)
    print("result")
    print(result)
    return prediction, result  # 예측된 레이블(Fake/Real)과 confidence 값 반환

# 예시 코드
if __name__ == '__main__':
    model_path = './DCS_freqnet.pth'  # 모델 경로 설정
    image_path = './images/input_image.png'  # 이미지 경로 설정
    cuda = True  # CUDA 사용 여부

    # 함수 호출
    prediction, result = run_freqnet_detection(model_path, image_path, cuda)

    # 결과 출력
    print(f"Prediction: {'Fake' if prediction == 1 else 'Real'}")
    print(f"Confidence: Real = {result[0]:.4f}, Fake = {result[1]:.4f}")
