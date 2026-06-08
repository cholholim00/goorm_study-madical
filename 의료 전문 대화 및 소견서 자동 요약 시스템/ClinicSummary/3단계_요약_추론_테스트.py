import os
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

def test_inference():
    print("⏳ [System] 36k 벌크 학습이 완료된 KoBART 요약 가중치 로드 중...")
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    MODEL_PATH = "model/best_summary_model"
    
    if not os.path.exists(MODEL_PATH):
        print(f"❌ [{MODEL_PATH}] 폴더를 찾을 수 없습니다.")
        return

    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_PATH).to(device)
    model.eval()
    print("🟢 [System] 고성능 임상 요약 생성 엔진 준비 완료!")

    # 🧪 실전 의료 대화 테스트 샘플
    sample_text = (
        "안녕하세요 의사 선생님. 제가 며칠 전부터 아랫배가 쿡쿡 쑤시고 생리 주기가 아닌데도 "
        "부정출혈이 조금씩 나와서 너무 걱정돼서 왔어요. 통증은 밤에 특히 심해지는 것 같습니다. "
        "의사 소견으로는 자궁 초음파 검사를 진행해서 정밀하게 상태를 확인해 볼 필요가 있겠습니다. "
        "또한 검사 결과가 나오기 전까지는 무리한 운동을 피하고 처방해 드리는 진통 소염제를 복용하면서 "
        "안정을 취하셔야 합니다. 일주일 뒤에 검사 결과 보러 다시 내원하세요."
    )

    print("\n" + "="*50)
    print(f"📝 [입력된 진료 대화 본문]:\n{sample_text}")
    print("="*50)

    inputs = tokenizer(sample_text, return_tensors="pt", max_length=512, truncation=True).to(device)

    print("⚡ [Inference] AI 소견 요약 연산 작동 중...")
    
    with torch.no_grad():
        summary_ids = model.generate(
            inputs["input_ids"],
            do_sample=True,             
            top_k=30,                   
            top_p=0.85,                 
            temperature=0.6,            
            
            max_length=100,             # 🚨 85에서 100으로 살짝 상향하여 마지막 문장 완성 유도
            min_length=20,              
            repetition_penalty=3.5,     
            no_repeat_ngram_size=2,     
            
            # UserWarning을 유발하던 빔 서치 전용 옵션(early_stopping, length_penalty) 제거
            eos_token_id=tokenizer.eos_token_id
        )

    generated_summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    
    print("\n✨ [AI 의료 가중치가 자동 생성해 낸 환자 요약 소견서]:")
    print(f"👉 {generated_summary}")
    print("="*50)

if __name__ == "__main__":
    test_inference()