# eval_xray.py
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
import matplotlib.pyplot as plt

# ===== 경로 설정 =====
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "models" / "xray_mobilenetv2_best.h5"

# 👉 테스트 이미지 폴더 (필요하면 여기만 수정하면 됨)
# 예: D:\medical_project\chest_xray\test\NORMAL\...
TEST_DIR = BASE_DIR / "chest_xray"  / "test"

IMG_SIZE = (160, 160)
BATCH_SIZE = 32


def main():
    print("=== X-ray 모델 성능 평가 시작 ===")
    print(f"[INFO] 모델 경로: {MODEL_PATH}")
    print(f"[INFO] 테스트 데이터 경로: {TEST_DIR}")

    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"모델 파일을 찾을 수 없습니다: {MODEL_PATH}")

    if not TEST_DIR.exists():
        raise FileNotFoundError(f"테스트 폴더를 찾을 수 없습니다: {TEST_DIR}")

    # ----- 데이터 로더 -----
    datagen = ImageDataGenerator(rescale=1.0 / 255.0)

    test_gen = datagen.flow_from_directory(
        TEST_DIR,
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode="binary",  # NORMAL vs PNEUMONIA
        shuffle=False,        # 순서 고정 (y_true와 맞추려고)
    )

    print(f"[INFO] class_indices: {test_gen.class_indices}")
    # 예: {'NORMAL': 0, 'PNEUMONIA': 1}

    # ----- 모델 로딩 -----
    print("[INFO] 모델 로드 중...")
    model = tf.keras.models.load_model(MODEL_PATH)
    print("[INFO] 모델 로드 완료")

    # ----- 예측 -----
    steps = int(np.ceil(test_gen.samples / BATCH_SIZE))
    print(f"[INFO] 테스트 샘플 수: {test_gen.samples}, steps: {steps}")

    y_prob = model.predict(test_gen, steps=steps)
    y_prob = y_prob.reshape(-1)  # (N, 1) -> (N,)

    # threshold 0.5 기준 이진화
    y_pred = (y_prob >= 0.5).astype(int)
    y_true = test_gen.classes  # directory 구조 기준 실제 라벨 (0/1)

    # 필요하면 길이 맞추기 (안전장치)
    n = min(len(y_true), len(y_pred))
    y_true = y_true[:n]
    y_pred = y_pred[:n]
    y_prob = y_prob[:n]

    # ----- 지표 계산 -----
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    cm = confusion_matrix(y_true, y_pred)

    print("\n=== X-ray 테스트 결과 ===")
    print(f"Accuracy : {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall   : {rec:.4f}")
    print(f"F1-score : {f1:.4f}")
    print("\nConfusion Matrix:")
    print(cm)

    # 클래스 이름 매핑
    idx_to_class = {v: k for k, v in test_gen.class_indices.items()}
    target_names = [idx_to_class[i] for i in range(len(idx_to_class))]

    print("\n=== Classification Report ===")
    print(classification_report(y_true, y_pred, target_names=target_names, digits=4))

    # ----- Confusion Matrix 그림으로 저장 -----
    save_dir = BASE_DIR / "reports"
    save_dir.mkdir(exist_ok=True)
    cm_path = save_dir / "xray_confusion_matrix.png"

    fig, ax = plt.subplots(figsize=(4, 4))
    im = ax.imshow(cm, cmap="Blues")

    ax.set_xticks(np.arange(len(target_names)))
    ax.set_yticks(np.arange(len(target_names)))
    ax.set_xticklabels(target_names)
    ax.set_yticklabels(target_names)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title("X-ray Confusion Matrix")

    # 숫자 표시
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(
                j,
                i,
                cm[i, j],
                ha="center",
                va="center",
                color="black",
            )

    fig.colorbar(im, ax=ax)
    plt.tight_layout()
    fig.savefig(cm_path, dpi=200)
    plt.close(fig)

    print(f"\n[INFO] Confusion Matrix 이미지 저장: {cm_path}")
    print("[INFO] X-ray 평가 완료 ✅")


if __name__ == "__main__":
    main()
