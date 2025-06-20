from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from utils.predict import predict_video

# FastAPI 앱 실행

app = FastAPI()

@app.post("/predict")
async def predict(video: UploadFile = File(...)):
    contents = await video.read()  # 업로드된 영상 내용을 바이트로 읽음
    fake_prob = predict_video(contents)  # 영상 분석 → 확률 반환
    return JSONResponse(content={"fake_prob": fake_prob})


@app.get("/")
def 작명():
    return 'hello'

