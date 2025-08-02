from pydantic import BaseModel
from typing import Optional


class DetectionRunResponse(BaseModel):
    detectionId: str
    message: str

class DetectionResultData(BaseModel):
    isDeepfake: bool                 # 딥페이크 여부
    confidence: float                # 딥페이크 확률 (0.0 ~ 1.0)
    imageUrl: Optional[str] = None   # 업로드된 이미지 URL (ex: /static/uploads/abc.png)
    gradcamUrl: Optional[str] = None # Grad-CAM 히트맵 URL (ex: /static/uploads/abc_gradcam.png)
    details: Optional[str] = None    # 내부 설명용 문자열 (파일명 포함 등)  
                                        # imageUrl과 gradcamUrl을 파싱을 통해 동적으로 생성하고 있기 때문에 반드시 필요


class DetectionResultResponse(BaseModel):
    detectionId: str
    result: DetectionResultData
