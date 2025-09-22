# server/app/routers/main.py

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from starlette.status import HTTP_401_UNAUTHORIZED
from app.utils.auth import decode_access_token  # ✅ 변경된 import
from app.schemas.main import MainPageResponse, ButtonPaths

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

@router.get("/mainPage", response_model=MainPageResponse)
def get_main_page_info(token: str = Depends(oauth2_scheme)):
    # ✅ JWT 검증 - 새 방식 적용
    payload = decode_access_token(token)
    user_id = payload.get("sub") if payload else None
    if not user_id:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid token")

    return MainPageResponse(
        buttons=ButtonPaths(
            myPage="/users/me",
            deepfakeDetection="/detections",
            quiz="/quiz"
        )
    )
