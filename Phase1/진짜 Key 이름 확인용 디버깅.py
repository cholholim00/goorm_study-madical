import json
from pathlib import Path

DATA_DIR = r"dataset/초거대AI 사전학습용 헬스케어 질의응답 데이터/개방데이터/데이터/Training/라벨링데이터/TL/1.질문"

# 딱 하나의 파일만 매핑해서 구조를 봅니다.
sample_file = next(Path(DATA_DIR).glob("**/*.json"))

print(f"📄 샘플 파일 경로: {sample_file}")
print("-" * 50)

with open(sample_file, "r", encoding="utf-8") as f:
    sample_data = json.load(f)
    
    # 1. 최상위 Key들 확인
    print(f"🔑 최상위 Key 목록: {list(sample_data.keys())}")
    print("-" * 50)
    
    # 2. 구조 데이터 일부 출력 (최대 600자만 잘라서 보기)
    print("📝 JSON 내부 실제 내용 샘플:")
    print(json.dumps(sample_data, indent=2, ensure_ascii=False)[:600])