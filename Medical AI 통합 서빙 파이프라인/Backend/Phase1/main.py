import os
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from sklearn.preprocessing import LabelEncoder
import pandas as pd

def load_inference_pipeline():
    # 1. 고도화 학습이 완료된 모델 경로 지정
    MODEL_PATH = "model/best_baseline_model"
    DATA_CSV = "dataset/데이터 파싱자료/parsed_medical_sample.csv"
    
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"❌ '{MODEL_PATH}' 경로에 고도화 모델이 없습니다. 먼저 학습을 완료해주세요.")
        
    print("🔄 의료 진단 AI 분류 엔진 로드 중...")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # 2. 토크나이저 및 모델 로드
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
    model.to(device)
    model.eval()  # ✨ 추론 모드로 전환 (Dropout, BatchNorm 비활성화)
    
    # 3. 데이터셋에서 사용했던 클래스 매핑 재현
    df = pd.read_csv(DATA_CSV)
    label_encoder = LabelEncoder()
    label_encoder.fit(df["label"])
    
    print(f"✅ AI 엔진 로드 완료! (구동 디바이스: {device})")
    print(f"🏥 지원하는 진료과 종류: {len(label_encoder.classes_)}개 카테고리")
    print("-" * 60)
    
    return tokenizer, model, label_encoder, device

def predict_department(text, tokenizer, model, label_encoder, device):
    # 문장 토큰화 및 텐서 변환
    inputs = tokenizer(
        text, 
        return_tensors="pt", 
        truncation=True, 
        padding="max_length", 
        max_length=128
    )
    
    # 데이터를 GPU/CPU 디바이스로 이동
    inputs = {k: v.to(device) for k, v in inputs.items()}
    
    with torch.no_grad():  # 추론 시 가중치 업데이트 방지 (메모리 절약)
        outputs = model(**inputs)
        logits = outputs.logits
        
        # Softmax를 통하여 각 클래스별 확률 변환 (%)
        probabilities = F.softmax(logits, dim=-1).squeeze().tolist()
        
    # 가장 높은 확률을 가진 인덱스 추출
    pred_idx = torch.argmax(logits, dim=-1).item()
    pred_label = label_encoder.inverse_transform([pred_idx])[0]
    confidence = probabilities[pred_idx] * 100
    
    return pred_label, confidence, probabilities

if __name__ == "__main__":
    try:
        tokenizer, model, label_encoder, device = load_inference_pipeline()
        
        print("💡 [Medical AI 안내 시스템] 조율이 끝났습니다.")
        print("💡 증상을 자유롭게 입력하세요. (종료하려면 'q' 또는 'quit' 입력)")
        print("-" * 60)
        
        while True:
            user_input = input("\n🩺 환자 증상 입력: ").strip()
            
            if user_input.lower() in ["q", "quit", "종료"]:
                print("👋 Medical AI 시스템을 종료합니다. 건강하세요!")
                break
                
            if not user_input:
                print("⚠️ 증상을 한 줄이라도 입력해 주세요.")
                continue
                
            # AI 예측 실행
            department, score, all_probs = predict_department(
                user_input, tokenizer, model, label_encoder, device
            )
            
            # 결과 출력
            print(f"📢 [AI 진단 결과]: 해당 증상은 종합 분석 결과 \033[92m[{department}]\033[0m으로 분류됩니다.")
            print(f"📊 [판단 신뢰도]: {score:.2f}%")
            
    except Exception as e:
        print(e)