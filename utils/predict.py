import numpy as np

def predict_video(video_bytes: bytes) -> float:
    # [TODO] 실제로는 OpenCV로 프레임 추출 후 모델 추론할 부분
    # 지금은 임시로 0~1 사이의 무작위 확률 반환
    return np.random.uniform(0.0, 1.0)
