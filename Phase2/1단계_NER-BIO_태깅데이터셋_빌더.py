import json
import os
import random
import pandas as pd
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm

def convert_to_bio_tags(text, entities):
    """문장과 entities 정보를 바탕으로 글자 단위 BIO 태그 리스트를 생성하는 함수"""
    # 기본적으로 모든 글자를 'O' (Outside)로 초기화
    bio_tags = ["O"] * len(text)
    
    # 겹치는 개체명이 있을 경우를 대비해 길이 순으로 정렬
    entities = sorted(entities, key=lambda x: x.get("position", 0))
    
    for entity_info in entities:
        start_idx = entity_info.get("position")
        entity_text = entity_info.get("text")
        entity_type = entity_info.get("entity") # 예: '질환명', '의약품' 등
        
        if start_idx is None or not entity_text or not entity_type:
            continue
            
        end_idx = start_idx + len(entity_text)
        
        # 문장 범위를 벗어나는 예외 처리
        if end_idx > len(text):
            continue
            
        # BIO 태깅 적용
        # 첫 글자는 B-(Begin), 나머지 글자는 I-(Inside)
        bio_tags[start_idx] = f"B-{entity_type}"
        for i in range(start_idx + 1, end_idx):
            bio_tags[i] = f"I-{entity_type}"
            
    return bio_tags

def parse_ner_json(file_path):
    """단일 JSON 파일에서 문장과 BIO 태그 데이터를 추출하는 함수"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            text = data.get("question")
            entities = data.get("entities", [])
            
            if text and isinstance(entities, list):
                text = str(text).strip()
                bio_tags = convert_to_bio_tags(text, entities)
                
                # 공백 조인 대신 진짜 리스트 구조를 보존하여 직렬화
                tokens_list = list(text)
                
                return {
                    "tokens": json.dumps(tokens_list, ensure_ascii=False), 
                    "ner_tags": json.dumps(bio_tags, ensure_ascii=False)
                }
    except Exception:
        pass
    return None

if __name__ == "__main__":
    DATA_DIR = r"../Phase1/dataset/초거대AI 사전학습용 헬스케어 질의응답 데이터/개방데이터/데이터/Training/라벨링데이터/TL/1.질문"
    SAMPLE_SIZE = 25000  # Phase 1 고도화 데이터 체급과 맞추기 위한 샘플 수
    
    print("🔍 1단계: 전체 JSON 파일 스캔 중...")
    all_files = list(Path(DATA_DIR).glob("**/*.json"))
    
    if len(all_files) > SAMPLE_SIZE:
        random.seed(42)
        sampled_files = random.sample(all_files, SAMPLE_SIZE)
    else:
        sampled_files = all_files
        
    print(f"⚡ 2단계: 멀티프로세싱 가동... {len(sampled_files):,}개 파일 BIO 태깅 변환 중")
    
    with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
        results = list(tqdm(executor.map(parse_ner_json, sampled_files), total=len(sampled_files)))
        
    # 데이터 정리
    tokens_list, tags_list = [], []
    for res in results:
        if res:
            tokens_list.append(res["tokens"])
            tags_list.append(res["ner_tags"])
            
    df = pd.DataFrame({"tokens": tokens_list, "ner_tags": tags_list})
    
    print(f"\n✅ NER 데이터셋 파싱 완료! 총 유효 문장 수: {len(df):,}개")
    
    # 데이터 구조 확인을 위한 출력
    print("\n🔍 파싱된 데이터 상위 3개 미리보기")
    print("-" * 60)
    for i in range(min(3, len(df))):
        print(f"📝 문장 (글자 단위 분할):\n{df['tokens'].iloc[i]}")
        print(f"🏷️ BIO 태그 대응:\n{df['ner_tags'].iloc[i]}")
        print("-" * 60)
        
    # 다음 학습 단계를 위해 CSV 저장
    df.to_csv("dataset/ner_medical_dataset.csv", index=False, encoding="utf-8-sig")
    print("💾 NER 데이터셋이 'dataset/ner_medical_dataset.csv'로 무사히 저장되었습니다.")