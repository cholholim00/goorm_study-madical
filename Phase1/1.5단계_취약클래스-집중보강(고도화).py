import json
import os
import random
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from transformers.trainer_pt_utils import LabelSmoother
from datasets import Dataset

# 1. GPU 및 환경 설정
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"📟 활성화된 디바이스: {device} (RTX 4060 Ti 가속 준비)")

# 2. 고도화된 데이터 파싱 로직 (약점 클래스 타겟팅)
def parse_single_json(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            text = data.get("question")
            label = data.get("disease_category")
            if text and label:
                return {"text": str(text).strip(), "label": str(label).strip()}
    except Exception:
        pass
    return None

if __name__ == "__main__":
    DATA_DIR = r"dataset/초거대AI 사전학습용 헬스케어 질의응답 데이터/개방데이터/데이터/Training/라벨링데이터/TL/1.질문"
    
    print("🔍 1단계: 전체 JSON 파일 스캔 중...")
    all_files = list(Path(DATA_DIR).glob("**/*.json"))
    
    # 클래스별로 파일들을 분류합니다.
    print("📂 질환 카테고리별 파일 분류 중...")
    category_files = {}
    for f_path in tqdm(all_files):
        # 경로명에 질환 이름이 포함되어 있는 특성을 이용해 빠르게 분류
        parts = f_path.parts
        # '1.질문' 다음 폴더명이 질환 카테고리입니다.
        try:
            idx = parts.index("1.질문")
            category = parts[idx+1]
            if category not in category_files:
                category_files[category] = []
            category_files[category].append(f_path)
        except Exception:
            continue

    # 🎲 약점 클래스는 더 많이, 잘 맞추는 클래스는 적당히 샘플링 (데이터 밸런싱)
    selected_files = []
    random.seed(42)
    
    print("\n⚖️ 클래스별 목표 데이터 수집 (오답노트 빌드)")
    for cat, files in category_files.items():
        # 약점이었던 여성질환과 응급질환은 원본 풀에서 최대한 많이 확보 (기존의 약 4~5배)
        if cat in ["여성질환", "응급질환"]:
            target_size = min(4000, len(files)) 
        elif cat in ["치과질환", "유전질환", "성형미용 및 재건"]:
            target_size = min(800, len(files))
        else:
            target_size = min(1500, len(files)) # 일반 클래스 상한선 조정
            
        sampled = random.sample(files, target_size)
        selected_files.extend(sampled)
        print(f" - [{cat}]: {len(sampled)}개 파일 채택 완료")

    print(f"\n⚡ 총 {len(selected_files):,}개 고도화 데이터 병렬 파싱 시작...")
    with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
        results = list(tqdm(executor.map(parse_single_json, selected_files), total=len(selected_files)))
        
    sentences, labels = [], []
    for res in results:
        if res:
            sentences.append(res["text"])
            labels.append(res["label"])
            
    df = pd.DataFrame({"text": sentences, "label": labels})
    
    # 3. 라벨 인코딩 및 가중치 계산
    label_encoder = LabelEncoder()
    df["label_idx"] = label_encoder.fit_transform(df["label"])
    num_labels = len(label_encoder.classes_)
    
    # CrossEntropy에 주입할 클래스별 역가중치 계산
    class_counts = df["label_idx"].value_counts().sort_index().values
    total_samples = len(df)
    class_weights = total_samples / (num_labels * class_counts)
    class_weights_tensor = torch.tensor(class_weights, dtype=torch.float32).to(device)
    
    # 4. 데이터셋 분리 및 토큰화
    train_df, val_df = train_test_split(df, test_size=0.2, random_state=42, stratify=df["label_idx"])
    train_dataset = Dataset.from_pandas(train_df)
    val_dataset = Dataset.from_pandas(val_df)
    
    MODEL_NAME = "klue/roberta-large"
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    
    def tokenize_function(examples):
        return tokenizer(examples["text"], truncation=True, padding="max_length", max_length=128)
        
    tokenized_train = train_dataset.map(tokenize_function, batched=True)
    tokenized_val = val_dataset.map(tokenize_function, batched=True)
    
    tokenized_train = tokenized_train.rename_column("label_idx", "labels").remove_columns(["text", "label", "__index_level_0__"])
    tokenized_val = tokenized_val.rename_column("label_idx", "labels").remove_columns(["text", "label", "__index_level_0__"])
    
    # 5. 🔥 [핵심] 클래스 가중치 손실 함수를 반영한 Custom Trainer 정의
    class CustomTrainer(Trainer):
        def compute_loss(self, model, inputs, return_outputs=False):
            labels = inputs.get("labels")
            outputs = model(**inputs)
            logits = outputs.get("logits")
            # 1단계에서 계산한 class_weights_tensor를 손실함수에 직접 주입!
            loss_fct = nn.CrossEntropyLoss(weight=class_weights_tensor)
            loss = loss_fct(logits.view(-1, self.model.config.num_labels), labels.view(-1))
            return (loss, outputs) if return_outputs else loss

    # 6. 모델 및 학습 인자 로드
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=num_labels)
    model.to(device)
    
    def compute_metrics(eval_pred):
        predictions, labels = eval_pred
        preds = np.argmax(predictions, axis=1)
        return {"accuracy": (preds == labels).mean()}
        
    training_args = TrainingArguments(
        output_dir="./results_advanced",
        evaluation_strategy="epoch",
        save_strategy="epoch",
        learning_rate=2e-5,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        gradient_accumulation_steps=2,
        num_train_epochs=3,
        weight_decay=0.01,
        fp16=True,
        logging_steps=50,
        load_best_model_at_end=True,
        metric_for_best_model="accuracy",
        report_to="none"
    )
    
    trainer = CustomTrainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_train,
        eval_dataset=tokenized_val,
        compute_metrics=compute_metrics,
    )
    
    print("\n🏋️ [고도화 레이스] 약점 극복 커스텀 학습을 시작합니다!")
    trainer.train()
    
    # 7. 모델 저장
    model.save_pretrained("model/best_baseline_model")
    tokenizer.save_pretrained("model/best_baseline_model")
    print("💾 가장 성능이 좋은 베이스라인 모델이 'model/best_baseline_model'에 저장되었습니다!")