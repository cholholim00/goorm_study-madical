import os
from pathlib import Path

import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
)

# ===== 경로 설정 =====
BASE_DIR = Path(__file__).resolve().parent
DATA_ROOT = BASE_DIR / "chest_xray"

# chest_xray/test 또는 chest_xray/chest_xray_processed/test 둘 다 지원
if (DATA_ROOT / "test").is_dir():
    TEST_DIR = DATA_ROOT / "test"
elif (DATA_ROOT / "chest_xray_processed" / "test").is_dir():
    TEST_DIR = DATA_ROOT / "chest_xray_processed" / "test"
else:
    raise FileNotFoundError(
        f"test 데이터 폴더를 찾을 수 없습니다.\n"
        f"기대하는 위치:\n"
        f" - {DATA_ROOT / 'test'}\n"
        f" - {DATA_ROOT / 'chest_xray_processed' / 'test'}"
    )

MODEL_PATH = BASE_DIR / "models" / "xray_mobilenetv2_best.h5"
IMG_SIZE = (160, 160)
BATCH_SIZE = 8


def load_model():
    if not MODEL_PATH.is_file():
        raise FileNotFoundError(f"모델 파일을 찾을 수 없습니다: {MODEL_PATH}")
    print(f"[INFO] 모델 로드 중: {MODEL_PATH}")
    model = tf.keras.models.load_model(MODEL_PATH.as_posix(), compile=False)
    print("[INFO] 모델 로드 완료")
    return model


def main():
    # ===== 데이터 로더 =====
    datagen = ImageDataGenerator(rescale=1.0 / 255)

    test_gen = datagen.flow_from_directory(
        TEST_DIR,
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode="binary",
        shuffle=False,  # 중요! 순서 고정
    )

    print("Class indices:", test_gen.class_indices)

    model = load_model()

    # ===== 예측 =====
    print("[INFO] test 데이터셋 예측 중...")
    probs = model.predict(test_gen, verbose=1).ravel()  # (N,)
    y_pred = (probs >= 0.5).astype(int)
    y_true = test_gen.classes  # DirectoryIterator에서 제공

    # ===== 지표 계산 =====
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred)
    rec = recall_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred)
    cm = confusion_matrix(y_true, y_pred)

    print("\n=== Test Set Performance ===")
    print(f"Accuracy : {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall   : {rec:.4f}")
    print(f"F1-score : {f1:.4f}")

    print("\nConfusion Matrix (rows=true, cols=pred)")
    print(cm)

    print("\nClassification Report")
    target_names = [cls for cls, idx in sorted(test_gen.class_indices.items(), key=lambda x: x[1])]
    print(classification_report(y_true, y_pred, target_names=target_names))


if __name__ == "__main__":
    main()
