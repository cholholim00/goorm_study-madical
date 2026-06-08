import os
from huggingface_hub import HfApi

# 1. 원본 Phase 1 가공 데이터셋 경로 타겟팅
local_csv_path = "./의료 전문 대화 및 소견서 자동 요약 시스템/"

if not os.path.exists(local_csv_path):
    print(f"❌ [{local_csv_path}] 파일을 찾을 수 없습니다. 경로를 확인하세요.")
    exit()

# 2. 허깅페이스 계정 설정 (★본인의 허깅페이스 실제 ID로 변경 필수★)
HF_USERNAME = "ghfla" 
DATASET_NAME = "korean-medical-classification-dataset"
dataset_repo_id = f"{HF_USERNAME}/{DATASET_NAME}"

api = HfApi()

print("⏳ [Dataset] 허깅페이스에 데이터셋 저장소 생성 중...")
api.create_repo(repo_id=dataset_repo_id, repo_type="dataset", exist_ok=True)

print("🚀 [Dataset] 가공 CSV 데이터셋 원격 업로드 시작...")
api.upload_file(
    path_or_fileobj=local_csv_path,
    path_in_repo="parsed_medical_sample.csv",
    repo_id=dataset_repo_id,
    repo_type="dataset"
)
print(f"✅ 데이터셋 업로드 완료! 주소: https://huggingface.co/datasets/{dataset_repo_id}")