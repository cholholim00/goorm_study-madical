import os
import json
import pandas as pd

def parse_single_json(file_path):
    """
    AI Hub 전문분야 멀티세션의 실제 내부 Key 구조인 
    [dialog -> utterance]와 [sessionSummary -> apprentice/wizard]를 정밀 추출합니다.
    """
    if not os.path.exists(file_path):
        print(f"❌ 파일을 찾을 수 없습니다: {file_path}")
        return None

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # 1. sessionInfo 레이어 진입 (실제 모든 노드가 여기에 집중되어 있음)
    session_info = data.get("sessionInfo", {})
    if isinstance(session_info, list) and len(session_info) > 0:
        session_info = session_info[0]
        
    if not isinstance(session_info, dict):
        print(f"⚠️ {file_path} 내부 sessionInfo 구조가 올바르지 않습니다.")
        return None

    # 2. 💬 대화 본문 스크립트 추출 (dialog -> utterance 탐색)
    dialog_list = session_info.get("dialog", [])
    full_text = " ".join([
        d.get("utterance", "").strip() 
        for d in dialog_list 
        if isinstance(d, dict) and d.get("utterance")
    ])
    
    # 3. 📝 요약문 추출 (sessionSummary -> apprentice & wizard 병합)
    session_summary = session_info.get("sessionSummary", {})
    summary_sentences = []
    
    if isinstance(session_summary, dict):
        # apprentice(초보자/환자 측면) 요약 라인 확보
        apprentice_list = session_summary.get("apprentice", [])
        if isinstance(apprentice_list, list):
            summary_sentences.extend([s.strip() for s in apprentice_list if s])
            
        # wizard(전문가/의사 측면) 요약 라인 확보
        wizard_list = session_summary.get("wizard", [])
        if isinstance(wizard_list, list):
            summary_sentences.extend([s.strip() for s in wizard_list if s])
            
    full_summary = " ".join(summary_sentences)

    # 데이터가 둘 다 성공적으로 확보되었을 때만 데이터셋 생성
    if full_text and full_summary:
        return {"text": full_text, "summary": full_summary}
    else:
        print(f"⚠️ {file_path} 파싱 실패 - 대화 길이: {len(full_text)}자 / 요약문 길이: {len(full_summary)}자")
        return None

if __name__ == "__main__":
    # 데이터 폴더 정의 및 결과 저장 경로
    TRAIN_JSON = "./data/train_data.json"
    VALID_JSON = "./data/valid_data.json"
    OUTPUT_DIR = "./data"
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # A. 훈련 데이터 파싱 및 CSV 변환
    print("⏳ [Train] 구조 저격 정제 엔진 가동...")
    train_result = parse_single_json(TRAIN_JSON)
    if train_result:
        train_df = pd.DataFrame([train_result])
        train_df.to_csv(os.path.join(OUTPUT_DIR, "summary_train.csv"), index=False, encoding="utf-8-sig")
        print("✅ 훈련용 [summary_train.csv] 셋 빌드 성공!")
        
    # B. 검증 데이터 파싱 및 CSV 변환
    print("\n⏳ [Valid] 구조 저격 정제 엔진 가동...")
    valid_result = parse_single_json(VALID_JSON)
    if valid_result:
        valid_df = pd.DataFrame([valid_result])
        valid_df.to_csv(os.path.join(OUTPUT_DIR, "summary_valid.csv"), index=False, encoding="utf-8-sig")
        print("✅ 검증용 [summary_valid.csv] 셋 빌드 성공!")