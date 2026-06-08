import os
from huggingface_hub import HfApi

# 1. 원본  고도화 모델 가중치 폴더 타겟팅
local_model_path = "./의료 전문 대화 및 소견서 자동 요약 시스템/ClinicSummary/model/best_summary_model"

if not os.path.exists(local_model_path):
    print(f"❌ [{local_model_path}] 폴더가 존재하지 않습니다. 경로를 확인하세요.")
    exit()

# 2. 허깅페이스 계정 설정 (★본인의 허깅페이스 실제 ID로 변경 필수★)
# 본인의 Hugging Face '계정 아이디(Username)'
HF_USERNAME = "ghfla"
# Hugging Face 레포지토리에 등록될 멋진 모델 이름 지정
MODEL_NAME = "kobart-v2-medical-summary"
model_repo_id = f"{HF_USERNAME}/{MODEL_NAME}"

api = HfApi()

print("⏳ [Model] 허깅페이스에 모델 저장소 생성 중...")
api.create_repo(repo_id=model_repo_id, repo_type="model", exist_ok=True)

print("🚀 [Model] 대용량 가중치 바이너리 폴더 업로드 시작 (시간이 다소 소요될 수 있습니다)...")
api.upload_folder(
    folder_path=local_model_path,
    repo_id=model_repo_id,
    repo_type="model"
)
print(f"✅ 모델 가중치 업로드 완료! 주소: https://huggingface.co/{model_repo_id}")