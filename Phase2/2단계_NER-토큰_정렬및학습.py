import json
import os
import ast
import numpy as np
import pandas as pd
import torch
from sklearn.model_selection import train_test_split
from transformers import AutoTokenizer, AutoModelForTokenClassification, Trainer, TrainingArguments
from datasets import Dataset

# 1. 환경 및 디바이스 세팅
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"📟 활성화된 디바이스: {device} (NER 학습 레이스 준비)")

if __name__ == "__main__":
    # 2. 파싱된 데이터셋 로드
    CSV_PATH = "dataset/ner_medical_dataset.csv"
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    
    # 저장할 때 문자열로 직렬화된 리스트를 진짜 파이썬 list 객체로 복원
    df["tokens"] = df["tokens"].apply(ast.literal_eval)
    df["ner_tags"] = df["ner_tags"].apply(ast.literal_eval)

    # 3. 고유 라벨(Label) 리스트 추출 및 매핑 사전 생성
    unique_tags = set()
    for tags in df["ner_tags"]:
        unique_tags.update(tags)
    
    # 인덱스 순서 고정을 위해 정렬 후 사전 생성
    tag_list = sorted(list(unique_tags))
    label2id = {tag: idx for idx, tag in enumerate(tag_list)}
    id2label = {idx: tag for tag, idx in label2id.items()}
    
    print(f"🏷️ 탐지된 고유 NER 태그 목록: {tag_list}")
    
    # 4. 데이터셋 분리 (Train 80% / Val 20%)
    train_df, val_df = train_test_split(df, test_size=0.2, random_state=42)
    train_dataset = Dataset.from_pandas(train_df)
    val_dataset = Dataset.from_pandas(val_df)

    # 5. 토크나이저 로드 및 정렬 함수 정의
    MODEL_NAME = "klue/roberta-large"
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    def tokenize_and_align_labels(examples):
        # 글자 리스트를 그대로 토크나이저에 주입 (is_split_into_words=True 활용)
        tokenized_inputs = tokenizer(
            examples["tokens"], 
            truncation=True, 
            padding="max_length", 
            max_length=128, 
            is_split_into_words=True
        )
        
        labels = []
        for i, label in enumerate(examples["ner_tags"]):
            word_ids = tokenized_inputs.word_ids(batch_index=i)
            previous_word_idx = None
            label_ids = []
            
            for word_idx in word_ids:
                if word_idx is None:
                    # [CLS], [SEP], [PAD] 같은 특수 토큰은 -100으로 채워 손실 함수 계산에서 제외
                    label_ids.append(-100)
                elif word_idx != previous_word_idx:
                    # 새로운 토큰이 시작되는 지점은 원본 라벨 적용
                    label_ids.append(label2id[label[word_idx]])
                else:
                    # 하나의 글자가 서브워드로 더 쪼개진 경우, 기존 라벨을 그대로 추종하거나 -100 처리
                    # 여기서는 완벽한 개체명 매핑을 위해 기존 라벨 인덱스를 추종하도록 세팅
                    label_ids.append(label2id[label[word_idx]])
                previous_word_idx = word_idx
            labels.append(label_ids)
            
        tokenized_inputs["labels"] = labels
        return tokenized_inputs

    print("✂️ 서브워드 토큰화 및 라벨 정렬 정밀 동기화 진행 중...")
    tokenized_train = train_dataset.map(tokenize_and_align_labels, batched=True, remove_columns=train_dataset.column_names)
    tokenized_val = val_dataset.map(tokenize_and_align_labels, batched=True, remove_columns=val_dataset.column_names)

    # 6. NER용 TokenClassification 모델 로드
    model = AutoModelForTokenClassification.from_pretrained(
        MODEL_NAME, 
        num_labels=len(tag_list),
        label2id=label2id,
        id2label=id2label
    )
    model.to(device)

    # 7. 학습 인자 및 Trainer 세팅
    training_args = TrainingArguments(
        output_dir="results_ner",
        evaluation_strategy="epoch",
        save_strategy="epoch",
        learning_rate=3e-5,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        gradient_accumulation_steps=2,
        num_train_epochs=3,
        weight_decay=0.01,
        fp16=True, # 4060 Ti 가속용 반정밀도 연산 활성화
        logging_steps=50,
        load_best_model_at_end=True,
        metric_for_best_model="loss", # NER은 기본 Loss 수렴을 기준으로 모니터링
        report_to="none"
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_train,
        eval_dataset=tokenized_val
    )

    print("\n🏋️ [Phase 2] 의료 개체명 인식(NER) 모델 학습을 시작합니다!")
    trainer.train()

    # 8. 완벽하게 학습된 NER 가중치 저장
    model.save_pretrained("model/best_ner_model")
    tokenizer.save_pretrained("model/best_ner_model")
    print("💾 의약 정보 추출용 NER 모델이 'model/best_ner_model'에 성공적으로 저장되었습니다!")