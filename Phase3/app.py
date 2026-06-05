# 1단계_FastAPI-멀티모델서빙
import os
import sys
import torch
import torch.nn.functional as F
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware  # 🎯 [CORS 패치 1] 미들웨어 임포트
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoModelForTokenClassification
from sklearn.preprocessing import LabelEncoder
import pandas as pd

# 1. FastAPI 앱 초기화
app = FastAPI(
    title="BridgeBoard Medical AI API",
    description="진료과 분류 및 개체명 추출(NER)을 동시에 수행하는 멀티 모델 서빙 서버"
)

# 🎯 [CORS 패치 2] React(보통 3000포트) 및 모든 도메인에서의 크로스 오리진 요청 허용 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 💡 나중에 실제 배포 시에는 React 주소만 정밀 지정 가능
    allow_credentials=True,
    allow_methods=["*"],  # GET, POST, OPTIONS 등 모든 메서드 허용
    allow_headers=["*"],  # 모든 HTTP 헤더 허용
)

# 2. 전역 변수 및 경로 세팅
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
models = {}

CLS_MODEL_PATH = "../Phase1/model/best_baseline_model"
NER_MODEL_PATH = "../Phase2/model/best_ner_model"  # 현재 Phase2 폴더 안이라면 이렇게 지정
DATA_CSV = "../Phase1/dataset/데이터 파싱자료/parsed_medical_sample.csv" 

@app.on_event("startup")
def load_all_models():
    """서버가 켜질 때 GPU 메모리에 두 모델을 동시에 적재(Warm-up)"""
    print("⏳ [System] 멀티 모델 가중치 로드 및 GPU 적재 시작...")
    try:
        # A. 진료과 분류 모델 로드
        models["cls_tokenizer"] = AutoTokenizer.from_pretrained(CLS_MODEL_PATH)
        models["cls_model"] = AutoModelForSequenceClassification.from_pretrained(CLS_MODEL_PATH).to(device)
        models["cls_model"].eval()
        
        # 진료과 라벨 복원용 Encoder 세팅
        df = pd.read_csv(DATA_CSV)
        le = LabelEncoder()
        le.fit(df["label"])
        models["label_encoder"] = le
        
        # B. NER 모델 로드
        models["ner_tokenizer"] = AutoTokenizer.from_pretrained(NER_MODEL_PATH)
        models["ner_model"] = AutoModelForTokenClassification.from_pretrained(NER_MODEL_PATH).to(device)
        models["ner_model"].eval()
        
        print("🚀 [System] 모든 AI 엔진이 CUDA 가속 레이어에 정상 적재되었습니다!")
    except Exception as e:
        print(f"❌ 모델 로드 중 에러 발생: {e}")
        sys.exit(1)

# 3. Request 데이터 검증 스펙
class MedicalRequest(BaseModel):
    text: str

# 4. 멀티 태스크 추론 엔드포인트
@app.post("/api/diagnose")
def diagnose_patient(request: MedicalRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="증상 텍스트가 비어있습니다.")
        
    text = request.text
    
    # --- [Task 1: 진료과 분류 추론] ---
    cls_tokenizer = models["cls_tokenizer"]
    cls_model = models["cls_model"]
    le = models["label_encoder"]
    
    cls_inputs = cls_tokenizer(text, return_tensors="pt", truncation=True, padding="max_length", max_length=128).to(device)
    with torch.no_grad():
        cls_outputs = cls_model(**cls_inputs)
        cls_probs = F.softmax(cls_outputs.logits, dim=-1).squeeze().tolist()
    
    pred_idx = torch.argmax(cls_outputs.logits, dim=-1).item()
    department = le.inverse_transform([pred_idx])[0]
    confidence = cls_probs[pred_idx] * 100
    
    # --- [Task 2: 의약/질환 정보 NER 추출] ---
    ner_tokenizer = models["ner_tokenizer"]
    ner_model = models["ner_model"]
    
    chars = list(text)
    ner_inputs = ner_tokenizer(chars, return_tensors="pt", truncation=True, padding="max_length", max_length=128, is_split_into_words=True)
    word_ids = ner_inputs.word_ids()
    ner_inputs = {k: v.to(device) for k, v in ner_inputs.items()}
    
    with torch.no_grad():
        ner_outputs = ner_model(**ner_inputs)
        ner_preds = torch.argmax(ner_outputs.logits, dim=-1).squeeze().tolist()
        
    extracted_entities = []
    current_entity = []
    current_type = None
    previous_word_idx = None
    
    for idx, word_idx in enumerate(word_ids):
        if word_idx is None or word_idx == previous_word_idx:
            continue
        pred_label = ner_model.config.id2label[ner_preds[idx]]
        char = chars[word_idx]
        
        if pred_label.startswith("B-"):
            if current_entity:
                extracted_entities.append({"text": "".join(current_entity), "type": current_type})
            current_entity = [char]
            current_type = pred_label.split("-")[1]
        elif pred_label.startswith("I-") and current_type == pred_label.split("-")[1]:
            current_entity.append(char)
        else:
            if current_entity:
                extracted_entities.append({"text": "".join(current_entity), "type": current_type})
                current_entity = []
                current_type = None
        previous_word_idx = word_idx
    if current_entity:
        extracted_entities.append({"text": "".join(current_entity), "type": current_type})

    # --- [최종 Response 통합 데이터 조립] ---
    return {
        "status": "success",
        "query": text,
        "classification": {
            "department": department,
            "confidence_score": round(confidence, 2)
        },
        "entities": extracted_entities
    }