import os
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

def test_inference():
    print("⏳ [System] 학습된 KoBART 요약 가중치 및 토크나이저 로드 중...")
    
    # 1. 연산 장치 세팅 및 훈련 완료된 모델 경로 조준
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    MODEL_PATH = "./model/best_summary_model"
    
    if not os.path.exists(MODEL_PATH):
        print(f"❌ [{MODEL_PATH}] 폴더를 찾을 수 없습니다. 2단계 학습 완료 여부를 확인하세요.")
        return

    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_PATH).to(device)
    model.eval()
    print("🟢 [System] 요약 생성 엔진이 추론 모드로 로드되었습니다!")

    # 2. 🧪 테스트용 의료 임상 대화 샘플 템플릿
    # (학습에 쓰인 구조와 유사한 장문 텍스트 예시입니다.)
    sample_text = (
        "안녕하세요 의사 선생님. 제가 며칠 전부터 아랫배가 쿡쿡 쑤시고 생리 주기가 아닌데도 "
        "부정출혈이 조금씩 나와서 너무 걱정돼서 왔어요. 통증은 밤에 특히 심해지는 것 같습니다. "
        "의사 소견으로는 자궁 초음파 검사를 진행해서 정밀하게 상태를 확인해 볼 필요가 있겠습니다. "
        "또한 검사 결과가 나오기 전까지는 무리한 운동을 피하고 처방해 드리는 진통 소염제를 복용하면서 "
        "안정을 취하셔야 합니다. 일주일 뒤에 검사 결과 보러 다시 내원하세요."
    )

    print("\n" + "="*50)
    print(f"📝 [입력된 원본 장문 스크립트]:\n{sample_text}")
    print("="*50)

    # 3. 인코더 입력 토크나이징 가속
    inputs = tokenizer(sample_text, return_tensors="pt", max_length=512, truncation=True).to(device)

    print("⚡ [Inference] Beam Search 생성 알고리즘 연산 가동...")
    
    # 4. 🎛️ 생성 퀄리티 제어를 위한 핵심 디코딩 하이퍼파라미터 튜닝
    with torch.no_grad():
        summary_ids = model.generate(
            inputs["input_ids"],
            num_beams=5,                
            max_length=40,              # 🚨 최대 길이를 더 타이트하게 조여서 강제 압축 유도
            min_length=15,              
            repetition_penalty=3.5,     # 🚨 패널티를 2.5 -> 3.5로 대폭 상향하여 본문 똑같이 베끼기 차단
            no_repeat_ngram_size=2,     # 🚨 2개 단어 연속 반복 절대 금지 (복사 차단 핵심)
            length_penalty=0.6,         # 🚨 짧고 명확한 문장을 선호하도록 피드백 가중치 부여 (소수점일 때 짧아짐)
            early_stopping=True         
        )

    # 5. 디코더 출력을 다시 인간의 언어로 디코딩
    generated_summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    
    print("\n✨ [AI 가중치가 축약해 낸 3줄 요약본]:")
    print(f"👉 {generated_summary}")
    print("="*50)

if __name__ == "__main__":
    test_inference()