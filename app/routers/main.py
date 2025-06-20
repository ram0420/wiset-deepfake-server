# /api/v1/main 라우터 (메인 페이지 데이터)
# server/app/routers/main.py

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from starlette.status import HTTP_401_UNAUTHORIZED
from app.utils.jwt_helper import decode_token

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

@router.get("/mainPage")
def get_main_page_info(token: str = Depends(oauth2_scheme)):
    # JWT 검증
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid token")

    return {
        "buttons": {
            "myPage": "/users/me",
            "deepfakeDetection": "/detections",
            "quiz": "/quiz"
        },
        "youtubeBanner": [
            {
                "videoId": "abc123",
                "title": "딥페이크 탐지란?",
                "thumbnailUrl": "https://img.youtube.com/vi/abc123/0.jpg"
            },
            {
                "videoId": "xyz789",
                "title": "AI 윤리 이야기",
                "thumbnailUrl": "https://img.youtube.com/vi/xyz789/0.jpg"
            }
        ]
    }
