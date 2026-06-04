import json
import os
import pandas as pd
import numpy as np
import random
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm
from sklearn.utils.class_weight import compute_class_weight

def parse_single_json(file_path):
    """단일 JSON 파일에서 disease_category와 question을 추출하는 함수"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
            # 실제 데이터 구조에 맞게 Key 매핑
            text = data.get("question")
            label = data.get("disease_category")
            
            if text and label:
                return {"text": str(text).strip(), "label": str(label).strip()}
    except Exception:
        pass
    return None

if __name__ == "__main__":
    DATA_DIR = r"dataset/초거대AI 사전학습용 헬스케어 질의응답 데이터/개방데이터/데이터/Training/라벨링데이터/TL/1.질문"
    SAMPLE_SIZE = 10000  # 🚀 빠른 베이스라인 검증을 위한 1차 샘플링 개수
    
    print(f"🔍 1단계: 전체 파일 목록 수집 중...")
    json_files = list(Path(DATA_DIR).glob("**/*.json"))
    total_files = len(json_files)
    print(f"✅ 총 {total_files:,}개의 JSON 파일을 발견했습니다.")
    
    if total_files > SAMPLE_SIZE:
        print(f"🎲 속도 최적화를 위해 이 중 {SAMPLE_SIZE:,}개를 무작위 샘플링합니다.")
        # 재현성을 위해 시드 고정
        random.seed(42)
        json_files = random.sample(json_files, SAMPLE_SIZE)
    
    print(f"⚡ 2단계: 멀티프로세싱 가동 (CPU 코어 풀가동)...")
    sentences, labels = [], []
    
    with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
        results = list(tqdm(executor.map(parse_single_json, json_files), total=len(json_files)))
        
    for res in results:
        if res:
            sentences.append(res["text"])
            labels.append(res["label"])
            
    # 데이터프레임 생성
    df = pd.DataFrame({"text": sentences, "label": labels})
    print(f"\n✅ 파싱 완료! 유효 데이터 개수: {len(df):,}개\n")
    
    if not df.empty:
        # [Challenge 1] 상위 샘플 미리보기
        print("🔍 1. 데이터 상위 5개 미리보기 (`df.head()`)")
        print(df.head())
        print("-" * 50)
        
        # [Challenge 2] 클래스 불균형 확인
        print("📊 2. 질환 카테고리별 분포 확인 (`df['label'].value_counts()`)")
        class_counts = df["label"].value_counts()
        print(class_counts)
        print("-" * 50)
        
        # 3. 모델 학습용 클래스 가중치 계산
        print("⚖️ 3. 모델 학습용 클래스 가중치(Class Weights) 계산")
        unique_classes = np.unique(df["label"])
        class_weights = compute_class_weight(
            class_weight="balanced",
            classes=unique_classes,
            y=df["label"].values
        )
        
        weight_dict = dict(zip(unique_classes, class_weights))
        for cls, weight in weight_dict.items():
            print(f" - [{cls}]: {weight:.4f}")
            
        # 4. 다음 단계를 위해 데이터 저장
        df.to_csv("dataset/데이터 파싱자료/parsed_medical_sample.csv", index=False, encoding="utf-8-sig")
        print("\n💾 파싱된 데이터를 'dataset/데이터 파싱자료/parsed_medical_sample.csv'로 저장했습니다.")