import os
from huggingface_hub import HfApi

# 1. 실행 경로 꼬임 방지를 위한 절대 경로 자동 계산
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 의료 전문 대화 및 소견서 자동 요약 시스템/ClinicSummary/data 내부를 직격
LOCAL_DATA_PATH = os.path.join(BASE_DIR, "의료 전문 대화 및 소견서 자동 요약 시스템", "ClinicSummary", "data")

# 만약 위 경로가 아니라 현재 가동 중인 작업 디렉토리에 data/ 폴더가 있다면 아래 주석을 해제하세요.
# LOCAL_DATA_PATH = os.path.join(BASE_DIR, "data")

# 2. 업로드할 핵심 요약 데이터셋 CSV 경로 매핑
train_csv_path = os.path.join(LOCAL_DATA_PATH, "summary_train.csv")
valid_csv_path = os.path.join(LOCAL_DATA_PATH, "summary_valid.csv")

# 파일 존재 여부 선제 타격 검증
if not os.path.exists(train_csv_path) or not os.path.exists(valid_csv_path):
    print(f"❌ [{LOCAL_DATA_PATH}] 구역 내부에 메인 CSV 파일들이 보이지 않습니다. 경로를 재점검하세요.")
    exit()

# 3. 허깅페이스 사용자 정보 등록
HF_USERNAME = "ghfla" 
DATASET_NAME = "korean-medical-dialogue-summary-dataset"
dataset_repo_id = f"{HF_USERNAME}/{DATASET_NAME}"

api = HfApi()

print(f"🚀 [Hugging Face] '{dataset_repo_id}' 데이터셋 원격 저장소 링크 빌드 중...")
api.create_repo(repo_id=dataset_repo_id, repo_type="dataset", exist_ok=True)

# 🎯 [핵심 패치] 36,000개 JSON을 생략하고, 정제 완료된 2개의 핵심 CSV만 단 2번의 API로 업로드 종료!
print("\n📦 [File 1/2] 훈련용 마스터 CSV (summary_train.csv) 수송 가동...")
api.upload_file(
    path_or_fileobj=train_csv_path,
    path_in_repo="summary_train.csv",  # 허깅페이스 허브 저장소에 노출될 파일명
    repo_id=dataset_repo_id,
    repo_type="dataset"
)
print("✅ summary_train.csv 원격 스트리밍 업로드 안착!")

print("\n📦 [File 2/2] 검증용 마스터 CSV (summary_valid.csv) 수송 가동...")
api.upload_file(
    path_or_fileobj=valid_csv_path,
    path_in_repo="summary_valid.csv",
    repo_id=dataset_repo_id,
    repo_type="dataset"
)
print("✅ summary_valid.csv 원격 스트리밍 업로드 안착!")

print(f"\n🎉 [Success] 허깅페이스 Rate Limit 규격을 우회하여 데이터셋 아카이빙 성공!")
print(f"🔗 데이터 허브 좌표: https://huggingface.co/datasets/{dataset_repo_id}")