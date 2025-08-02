# FastAPI 인스턴스 생성, 미들웨어 · 이벤트 등록

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import auth, main, user, detection, quiz
from fastapi.staticfiles import StaticFiles 
from app.routers import recommend 

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Deepfake Detection & Quiz Service")

# Static 파일 mount (꼭 있어야 함!)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
def read_root():
    return {"message": "Hello, Deepfake Detection & Quiz Service!"}

# CORS 설정 (필요시 origin 조절)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth.router)
app.include_router(main.router)
app.include_router(user.router)
app.include_router(detection.router)
app.include_router(quiz.router)
app.include_router(recommend.router)