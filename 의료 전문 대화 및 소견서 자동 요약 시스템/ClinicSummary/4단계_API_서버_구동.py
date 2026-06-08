import os
import torch
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import uvicorn

# Global 생성형 변수 사전 정의
model = None
tokenizer = None
device = None

# 1. 🛡️ [Lifespan 패치] DeprecationWarning을 방지하는 최신 비동기 수명 주기 핸들러
@asynccontextmanager
async def lifespan(app: FastAPI):
    global model, tokenizer, device
    print("⏳ [API Server] 로컬 디스크로부터 최적의 KoBART 가중치 스트리밍 중...")
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    MODEL_PATH = "model/best_summary_model"
    
    if not os.path.exists(MODEL_PATH):
        print(f"❌ [{MODEL_PATH}] 모델 경로가 존재하지 않습니다. 2, 3단계를 먼저 완수하세요.")
        os._exit(1)
        
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_PATH).to(device)
    model.eval()  # 추론 모드 고정
    print(f"🟢 [API Server] 생성형 AI 요약 모델 로드 완료! (연산 레이어: {device})")
    
    yield  # 🚀 서버 구동 상태 유지 레이어
    
    # 서버 종료 시 메모리 해제 로직 (필요 시)
    print("🛑 [API Server] 서버가 안전하게 가동 중지되었습니다.")

# 2. FastAPI 인스턴스 생성 시 lifespan 매핑
app = FastAPI(
    title="의료 전문 대화 및 소견서 자동 요약 API",
    description="KoBART 요약 서빙 백엔드 엔진입니다.",
    version="1.0.0",
    lifespan=lifespan
)

class DialogueRequest(BaseModel):
    text: str

class SummaryResponse(BaseModel):
    summary: str

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
                do_sample=True,             
                top_k=30,                   
                top_p=0.85,                 
                temperature=0.6,            
                max_length=100,             
                min_length=20,              
                repetition_penalty=3.5,     
                no_repeat_ngram_size=2,     
                eos_token_id=tokenizer.eos_token_id
            )
            
        generated_summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        return SummaryResponse(summary=generated_summary)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 추론 연산 중 장애 발생: {str(e)}")

if __name__ == "__main__":
    # 🚨 [Uvicorn 버그 패치] 파일명 스트링 주입 대신, 객체(app)를 직격하여 공백/한글 경로 버그 원천 차단
    uvicorn.run(app, host="127.0.0.1", port=8000)