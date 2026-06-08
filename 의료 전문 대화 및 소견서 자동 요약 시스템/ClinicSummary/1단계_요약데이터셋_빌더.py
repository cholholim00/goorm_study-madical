import os
import json
import glob
import pandas as pd
from tqdm import tqdm

def parse_single_json(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        session_info = data.get("sessionInfo", {})
        if isinstance(session_info, list) and len(session_info) > 0:
            session_info = session_info[0]
            
        if not isinstance(session_info, dict):
            return None

        # 1. 대화 본문 스크립트 추출 (dialog -> utterance)
        dialog_list = session_info.get("dialog", [])
        full_text = " ".join([
            d.get("utterance", "").strip() 
            for d in dialog_list 
            if isinstance(d, dict) and d.get("utterance")
        ])
        
        # 2. 요약문 추출 (sessionSummary -> apprentice & wizard)
        session_summary = session_info.get("sessionSummary", {})
        summary_sentences = []
        
        if isinstance(session_summary, dict):
            apprentice_list = session_summary.get("apprentice", [])
            if isinstance(apprentice_list, list):
                summary_sentences.extend([s.strip() for s in apprentice_list if s])
                
            wizard_list = session_summary.get("wizard", [])
            if isinstance(wizard_list, list):
                summary_sentences.extend([s.strip() for s in wizard_list if s])
                
        full_summary = " ".join(summary_sentences)

        if full_text and full_summary:
            return {"text": full_text, "summary": full_summary}
    except Exception:
        return None
    return None

if __name__ == "__main__":
    # 🎯 현재 내 프로젝트 내부의 data/ 폴더만 다이렉트 저격
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    
    print(f"📡 [직접 조준] 현재 수동 배치 타겟 폴더: {DATA_DIR}")
    
    # data/ 폴더 내부에 직접 흩뿌려진 모든 JSON 파일들을 긁어모음
    all_json_files = glob.glob(os.path.join(DATA_DIR, "*.json"))
    print(f"📂 포착된 총 JSON 파일 개수: {len(all_json_files)}개")
    
    if len(all_json_files) == 0:
        print("❌ 여전히 0개입니다! 파일 탐색기에서 ClinicSummary/data/ 폴더 안에 진짜로 .json 파일들을 복사해 넣었는지 다시 확인하세요.")
    else:
        # 데이터가 들어왔을 경우 절반은 Train, 절반은 Valid로 분할 처리하여 데이터 볼륨 생성
        parsed_records = []
        for file_path in tqdm(all_json_files, desc="임상 데이터 정제 중"):
            res = parse_single_json(file_path)
            if res:
                parsed_records.append(res)
                
        if parsed_records:
            # 8:2 비율로 분할하여 안정적인 벨런스 확보
            split_idx = int(len(parsed_records) * 0.8)
            train_records = parsed_records[:split_idx] if split_idx > 0 else parsed_records
            valid_records = parsed_records[split_idx:] if split_idx > 0 else parsed_records
            
            # Train CSV 빌드
            train_df = pd.DataFrame(train_records)
            train_df.to_csv(os.path.join(DATA_DIR, "summary_train.csv"), index=False, encoding="utf-8-sig")
            print(f"✅ 훈련용 [summary_train.csv] 생성 성공! (데이터: {len(train_df)}건)")
            
            # Valid CSV 빌드
            valid_df = pd.DataFrame(valid_records)
            valid_df.to_csv(os.path.join(DATA_DIR, "summary_valid.csv"), index=False, encoding="utf-8-sig")
            print(f"✅ 검증용 [summary_valid.csv] 생성 성공! (데이터: {len(valid_df)}건)")