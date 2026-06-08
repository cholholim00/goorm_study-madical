import os
import sys
import torch
import pandas as pd
from transformers import (
    AutoTokenizer, 
    AutoModelForSeq2SeqLM, 
    DataCollatorForSeq2Seq, 
    Seq2SeqTrainingArguments, 
    Seq2SeqTrainer
)
from datasets import Dataset

def train_kobart_summarization():
    print("⏳ [System] KoBART 요약 모델 학습 파이프라인 초기화 중...")
    
    # 1. 디바이스 세팅 및 GPU 가속 인프라 확인
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"📡 [System] 현재 연산 레이어: {device}")
    
    # 2. 가공된 CSV 데이터셋 로드
    train_csv = "./data/summary_train.csv"
    valid_csv = "./data/summary_valid.csv"
    
    if not os.path.exists(train_csv) or not os.path.exists(valid_csv):
        print("❌ [Error] 전처리된 CSV 파일을 찾을 수 없습니다. 1단계를 다시 확인하세요.")
        sys.exit(1)
        
    train_df = pd.read_csv(train_csv)
    valid_df = pd.read_csv(valid_csv)
    
    # Hugging Face Dataset 객체로 변환
    train_dataset = Dataset.from_pandas(train_df)
    valid_dataset = Dataset.from_pandas(valid_df)
    
    # 3. KoBART v2 토크나이저 및 베이스 가중치 로드
    MODEL_NAME = "gogamza/kobart-base-v2"
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME).to(device)
    
    # 4. Seq2Seq 전용 토크나이징 전처리 함수 정의
    def preprocess_function(examples):
        # 인코더 입력: 전체 대화 본문(text)
        inputs = [ex for ex in examples["text"]]
        # 디코더 입력/타겟: 정답 요약문(summary)
        targets = [ex for ex in examples["summary"]]
        
        # 문장 최대 길이 조절 (대화가 길 수 있으므로 max_length 지정)
        model_inputs = tokenizer(inputs, max_length=512, truncation=True, padding="max_length")
        
        # 디코더 타겟 토크나이징 (text_target 파라미터 활용)
        labels = tokenizer(text_target=targets, max_length=128, truncation=True, padding="max_length")
        
        model_inputs["labels"] = labels["input_ids"]
        return model_inputs

    print("✂️ [Data] 데이터셋 토큰 얼라인먼트 및 서브워드 쪼개기 진행 중...")
    tokenized_train = train_dataset.map(preprocess_function, batched=True, remove_columns=["text", "summary"])
    tokenized_valid = valid_dataset.map(preprocess_function, batched=True, remove_columns=["text", "summary"])
    
    # 5. 패딩 동기화를 위한 Dynamic Data Collator 세팅
    data_collator = DataCollatorForSeq2Seq(tokenizer, model=model, pad_to_multiple_of=8)
    
    # 6. 학습 하이퍼파라미터 지정 (Portable_GPU 환경에 맞춤 튜닝)
    training_args = Seq2SeqTrainingArguments(
        output_dir="./results",
        num_train_epochs=10,                # 테스트 및 빠른 수렴을 위해 10 에포크 지정
        per_device_train_batch_size=2,      # OOM 방지를 위한 안정적인 배치 사이즈
        per_device_eval_batch_size=2,
        warmup_steps=50,
        weight_decay=0.01,
        logging_dir="./logs",
        logging_steps=1,
        evaluation_strategy="epoch",        # 매 에포크 끝날 때마다 검증 진행
        save_strategy="epoch",
        load_best_model_at_end=True,
        predict_with_generate=True,         # 검증 시 실제 문장을 생성하도록 트리거
        fp16=torch.cuda.is_available(),     # 🚀 NVIDIA GPU 가속 엔진 (FP16 반정밀도 연산 패치)
        report_to="none"
    )
    
    # 7. 트레이너 엔진 가동
    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_train,
        eval_dataset=tokenized_valid,
        tokenizer=tokenizer,
        data_collator=data_collator
    )
    
    print("🔥 [Train] KoBART 생성 모델 학습 시작...")
    trainer.train()
    
    # 8. 최적의 모델 저장소 세팅
    SAVE_PATH = "./model/best_summary_model"
    model.save_pretrained(SAVE_PATH)
    tokenizer.save_pretrained(SAVE_PATH)
    print(f"🎉 [Success] 학습이 완료되어 최적의 가중치가 [{SAVE_PATH}]에 저장되었습니다!")

if __name__ == "__main__":
    train_kobart_summarization()