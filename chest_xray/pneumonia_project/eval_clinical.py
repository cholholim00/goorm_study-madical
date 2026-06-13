# eval_clinical.py
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
)

# ===== 경로 설정 =====
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "models" / "clinical_model.pkl"
DATA_PATH = BASE_DIR / "data" / "clinical_data.csv"  # 필요하면 수정

# CSV에서 타깃(정답) 컬럼 이름 (0/1)
TARGET_COL = "label"


def main():
    print("=== 임상 모델 성능 평가 시작 ===")
    print(f"[INFO] 모델 경로: {MODEL_PATH}")
    print(f"[INFO] 데이터 경로: {DATA_PATH}")

    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"모델 파일을 찾을 수 없습니다: {MODEL_PATH}")
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"임상 데이터 CSV를 찾을 수 없습니다: {DATA_PATH}")

    # ----- 모델 로딩 -----
    saved = joblib.load(MODEL_PATH)
    model = saved["model"]
    features = saved.get("features", ["age", "temp", "resp_rate", "spo2", "wbc", "crp"])

    print(f"[INFO] 사용 피처: {features}")

    # ----- 데이터 로딩 -----
    df = pd.read_csv(DATA_PATH)
    if df.empty:
        raise ValueError(
            f"임상 데이터 CSV({DATA_PATH})가 비어 있습니다. "
            "최소 한 줄 이상의 데이터를 넣어주세요."
        )

    # 필수 컬럼 체크
    missing_cols = [c for c in features + [TARGET_COL] if c not in df.columns]
    if missing_cols:
        raise ValueError(
            f"CSV에 다음 컬럼이 없습니다: {missing_cols}\n"
            f"현재 CSV 컬럼: {list(df.columns)}"
        )

    # 결측치 제거 (간단 버전)
    df = df.dropna(subset=features + [TARGET_COL])
    if df.empty:
        raise ValueError("필수 컬럼에 결측치 제거 후, 남은 데이터가 없습니다.")

    X = df[features]
    y = df[TARGET_COL].astype(int)

    # ----- 예측 -----
    if hasattr(model, "predict_proba"):
        y_prob = model.predict_proba(X)[:, 1]
    elif hasattr(model, "decision_function"):
        scores = model.decision_function(X)
        s_min, s_max = scores.min(), scores.max()
        y_prob = (scores - s_min) / (s_max - s_min + 1e-8)
    else:
        y_prob = None

    if y_prob is not None:
        y_pred = (y_prob >= 0.5).astype(int)
    else:
        y_pred = model.predict(X)

    # ----- 지표 계산 -----
    acc = accuracy_score(y, y_pred)
    prec = precision_score(y, y_pred, zero_division=0)
    rec = recall_score(y, y_pred, zero_division=0)
    f1 = f1_score(y, y_pred, zero_division=0)

    print("\n=== 임상 모델 테스트 결과 ===")
    print(f"Accuracy : {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall   : {rec:.4f}")
    print(f"F1-score : {f1:.4f}")

    if y_prob is not None:
        try:
            auc = roc_auc_score(y, y_prob)
            print(f"ROC-AUC  : {auc:.4f}")
        except Exception as e:
            print(f"[WARN] ROC-AUC 계산 중 오류: {e}")

    cm = confusion_matrix(y, y_pred)
    print("\nConfusion Matrix:")
    print(cm)

    print("\n=== Classification Report ===")
    print(classification_report(y, y_pred, digits=4))

    print("\n[INFO] 임상 모델 평가 완료 ✅")


if __name__ == "__main__":
    main()
