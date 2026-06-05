import torch
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from datasets import Dataset

# 1. 저장된 모델과 데이터 로드
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODEL_PATH = "model/best_baseline_model"

print("🔄 저장된 베이스라인 모델 및 토크나이저 로드 중...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
model.to(device)

# 데이터 다시 불러와서 검증셋(Val) 구조 재현
df = pd.read_csv("dataset/데이터 파싱자료/parsed_medical_sample.csv")
label_encoder = LabelEncoder()
df["label_idx"] = label_encoder.fit_transform(df["label"])

_, val_df = train_test_split(df, test_size=0.2, random_state=42, stratify=df["label_idx"])
val_dataset = Dataset.from_pandas(val_df)

# 2. 토큰화
def tokenize_function(examples):
    return tokenizer(examples["text"], truncation=True, padding="max_length", max_length=128)

tokenized_val = val_dataset.map(tokenize_function, batched=True)
tokenized_val = tokenized_val.rename_column("label_idx", "labels").remove_columns(["text", "label", "__index_level_0__"])

# 3. Trainer를 이용해 예측(Prediction) 수행
trainer = Trainer(model=model, args=TrainingArguments(output_dir="./tmp", per_device_eval_batch_size=16, fp16=True))

print("🔮 검증 데이터셋 예측 시작...")
predictions = trainer.predict(tokenized_val)
preds = np.argmax(predictions.predictions, axis=1)
true_labels = predictions.label_ids

# 4. 🔥 심층 레포트 출력
print("\n🎯 [최종 심층 검증 레포트] 질환별 상세 지표")
print("-" * 60)
report = classification_report(
    true_labels, 
    preds, 
    target_names=label_encoder.classes_,
    digits=4
)
print(report)