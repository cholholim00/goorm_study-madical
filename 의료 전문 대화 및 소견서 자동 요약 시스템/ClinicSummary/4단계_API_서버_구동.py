import os
import torch
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware # 🚨 추가
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import uvicorn

model = None
tokenizer = None
device = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model, tokenizer, device
    print("⏳ [API Server] 로컬 디스크로부터 최적의 KoBART 가중치 스트리밍 중...")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    MODEL_PATH = "model/best_summary_model"
    if not os.path.exists(MODEL_PATH):
        print(f"❌ [{MODEL_PATH}] 모델 경로가 존재하지 않습니다.")
        os._exit(1)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_PATH).to(device)
    model.eval()
    print(f"🟢 [API Server] 생성형 AI 요약 모델 로드 완료! (연산 레이어: {device})")
    yield
    print("🛑 [API Server] 서버가 안전하게 가동 중지되었습니다.")

app = FastAPI(
    title="의료 전문 대화 및 소견서 자동 요약 API",
    version="1.0.0",
    lifespan=lifespan
)

# 🚨 [신규 추가] 브라우저-서버 간 자바스크립트 네트워크 통신 차단 해제 (CORS 활성화)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 출처에서의 프론트엔드 요청 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DialogueRequest(BaseModel):
    text: str

class SummaryResponse(BaseModel):
    summary: str

@app.get("/dashboard", response_class=HTMLResponse)
def read_dashboard():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(BASE_DIR, "templates", "dashboard.html")
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="dashboard.html 파일을 찾을 수 없습니다.")

@app.get("/")
def health_check():
    return {"status": "healthy", "model": "KoBART-v2-Medical-Summary"}

@app.post("/api/summarize", response_model=SummaryResponse)
def summarize_clinic_dialogue(request: DialogueRequest):
    global model, tokenizer, device
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="요약할 대화 본문이 비어 있습니다.")
    try:
        inputs = tokenizer(request.text, return_tensors="pt", max_length=512, truncation=True).to(device)
        with torch.no_grad():
            summary_ids = model.generate(
                inputs["input_ids"],
                # 🚨 [확정적 디코딩 백전백승 패치] 
                # 주사위를 굴리지 않고 상위 확률 궤적만 추적하여 뜬금없는 노이즈 단어(교수명 등) 원천 차단
                num_beams=5,                
                max_length=90,              # 문장이 알맞게 끝나도록 타이트하게 제한
                min_length=20,              
                repetition_penalty=4.5,     # 🚨 페널티를 4.5로 극대화하여 뇌절 단어 유출 차단
                no_repeat_ngram_size=2,     # 2개 단어 연속 반복 절대 금지
                
                # 깔끔한 문장 종결 유도
                length_penalty=0.8,         
                early_stopping=True,        
                eos_token_id=tokenizer.eos_token_id
            )
        generated_summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        return SummaryResponse(summary=generated_summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 추론 연산 중 장애 발생: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)