import os
import torch
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from datasets import Dataset

# 1. GPU 장치 확인 및 PyTorch 환경 최적화 설정
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"📟 활성화된 디바이스: {device}")
if device.type == "cuda":
    print(f"🚀 학습에 사용할 GPU: {torch.cuda.get_device_name(0)}")
    # Windows 환경에서 GPU 연산 가속을 위한 설정
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True

# 2. 데이터 로드 및 라벨 인코딩
df = pd.read_csv("dataset/데이터 파싱자료/parsed_medical_sample.csv")

label_encoder = LabelEncoder()
df["label_idx"] = label_encoder.fit_transform(df["label"])
num_labels = len(label_encoder.classes_)

print(f"📊 총 클래스 개수: {num_labels}개")
print(f"🏷️ 인코딩된 클래스 매핑: {list(label_encoder.classes_)}")

# 3. Train / Validation 데이터셋 분리 (8:2 비율)
train_df, val_df = train_test_split(df, test_size=0.2, random_state=42, stratify=df["label_idx"])

# 4. Hugging Face Dataset 구조로 변환
train_dataset = Dataset.from_pandas(train_df)
val_dataset = Dataset.from_pandas(val_df)

# 5. 토크나이저 로드 (Challenge 1 정답 반영)
MODEL_NAME = "klue/roberta-large"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

def tokenize_function(examples):
    # 의료 데이터 특성상 문장이 아주 길지 않으므로 max_length는 128로 조절하여 VRAM 방어
    return tokenizer(examples["text"], truncation=True, padding="max_length", max_length=128)

print("✂️ 텍스트 토큰화 진행 중...")
tokenized_train = train_dataset.map(tokenize_function, batched=True)
tokenized_val = val_dataset.map(tokenize_function, batched=True)

# 모델 학습에 필요한 컬럼만 남기고 정리
tokenized_train = tokenized_train.rename_column("label_idx", "labels").remove_columns(["text", "label", "__index_level_0__"])
tokenized_val = tokenized_val.rename_column("label_idx", "labels").remove_columns(["text", "label", "__index_level_0__"])

# 6. 모델 로드 (분류 전용 로드)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=num_labels)
model.to(device)

# 7. 간단한 평가지표 함수 (Accuracy) 정의
def compute_metrics(eval_pred):
    predictions, labels = eval_pred
    preds = np.argmax(predictions, axis=1)
    return {"accuracy": (preds == labels).mean()}

# 8. RTX 4060 Ti 최적화 하이퍼파라미터 세팅
training_args = TrainingArguments(
    output_dir="모델/results",          # 모델 체크포인트 저장 폴더
    evaluation_strategy="epoch",     # 매 에폭마다 검증 진행
    save_strategy="epoch",           # 매 에폭마다 가중치 저장
    learning_rate=2e-5,              # BERT/RoBERTa 계열 표준 학습률
    per_device_train_batch_size=16,  # 4060 Ti 16GB에서 대형 모델 돌릴 때 안정적인 배치 크기
    per_device_eval_batch_size=16,
    gradient_accumulation_steps=2,   # 배치를 2번 누적하여 오차 역전파 수행 (실질 배치 사이즈 = 32 효과)
    num_train_epochs=3,              # 베이스라인이므로 3에폭만 가볍게 수행
    weight_decay=0.01,
    fp16=True,                       # ✨ RTX 4060 Ti 가속을 위한 핵심 (Mixed Precision) 옵션
    logging_steps=50,                # 50 스텝마다 로그 출력
    load_best_model_at_end=True,     # 학습 종료 시 가장 성적이 좋았던 모델 로드
    metric_for_best_model="accuracy",
    report_to="none"                 # 우선 WandB 없이 로컬 터미널로만 확인
)

# 9. Trainer 가동
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_train,
    eval_dataset=tokenized_val,
    compute_metrics=compute_metrics,
)

print("🏋️ 베이스라인 모델 학습을 시작합니다! (RTX 4060 Ti 구동)")
trainer.train()

# 10. 최종 베이스라인 모델 가중치 로컬 저장
model.save_pretrained("모델/best_baseline_model")
tokenizer.save_pretrained("모델/best_baseline_model")
print("💾 가장 성능이 좋은 베이스라인 모델이 '모델/best_baseline_model'에 저장되었습니다!")