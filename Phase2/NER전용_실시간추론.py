import os
import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification

def load_ner_pipeline():
    MODEL_PATH = "model/best_ner_model"
    
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"❌ '{MODEL_PATH}' 경로에 NER 모델이 없습니다.")
        
    print("🔄 의료 개체명 인식(NER) 엔진 로드 중...")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForTokenClassification.from_pretrained(MODEL_PATH)
    model.to(device)
    model.eval()
    
    print(f"✅ NER 엔진 로드 완료! (구동 디바이스: {device})")
    print("-" * 60)
    return tokenizer, model, device

def extract_entities(text, tokenizer, model, device):
    # 글자 단위 입력 모델이므로 list(text) 형태로 split 주입
    chars = list(text)
    inputs = tokenizer(
        chars, 
        return_tensors="pt", 
        truncation=True, 
        padding="max_length", 
        max_length=128, 
        is_split_into_words=True
    )
    
    # 🎯 [핵심 패치] dict로 변환되어 word_ids가 증발하기 전에 '미리' 추출해서 보관합니다.
    word_ids = inputs.word_ids()
    
    # 데이터를 GPU/CPU 디바이스로 이동 (이 순간 dict로 변환됨)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        predictions = torch.argmax(logits, dim=-1).squeeze().tolist()
        
    extracted_segments = []
    current_entity = []
    current_type = None
    
    previous_word_idx = None
    for idx, word_idx in enumerate(word_ids):
        if word_idx is None:
            continue
        
        # 중복 서브워드 토큰 처리 건너뛰기
        if word_idx == previous_word_idx:
            continue
            
        pred_id = predictions[idx]
        pred_label = model.config.id2label[pred_id]
        char = chars[word_idx]
        
        if pred_label.startswith("B-"):
            if current_entity:
                extracted_segments.append(("".join(current_entity), current_type))
            current_entity = [char]
            current_type = pred_label.split("-")[1]
        elif pred_label.startswith("I-") and current_type == pred_label.split("-")[1]:
            current_entity.append(char)
        else:
            if current_entity:
                extracted_segments.append(("".join(current_entity), current_type))
                current_entity = []
                current_type = None
        
        previous_word_idx = word_idx
        
    if current_entity:
        extracted_segments.append(("".join(current_entity), current_type))
        
    return extracted_segments

if __name__ == "__main__":
    try:
        tokenizer, model, device = load_ner_pipeline()
        
        print("💡 [Medical NER 시스템] 구동되었습니다.")
        print("💡 문장을 입력하면 주요 의료 개체(질환명 등)를 추출합니다. (종료: q)")
        print("-" * 60)
        
        while True:
            user_input = input("\n📝 문장 입력: ").strip()
            
            if user_input.lower() in ["q", "quit", "종료"]:
                print("👋 NER 시스템을 종료합니다.")
                break
                
            if not user_input:
                continue
                
            # 개체명 추출 실행
            entities = extract_entities(user_input, tokenizer, model, device)
            
            # 하이라이팅 출력 처리
            output_text = user_input
            if entities:
                print("\n🎯 [개체명 추출 결과]")
                for ent_text, ent_type in entities:
                    # 터미널에 초록색 배경/글씨로 하이라이팅 효과 부여
                    print(f" 📌 \033[92m[{ent_text}]\033[0m -> 종류: {ent_type}")
            else:
                print("\n🔍 추출된 의료 개체명이 없습니다.")
                
    except Exception as e:
        print(f"❌ 오류 발생: {e}")