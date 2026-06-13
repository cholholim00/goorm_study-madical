from pathlib import Path

import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, roc_auc_score

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" /"clinical_data.csv"
MODEL_DIR = BASE_DIR / "models"
MODEL_DIR.mkdir(exist_ok=True)
MODEL_PATH = MODEL_DIR / "clinical_model.pkl"

# 사용할 피처 컬럼들
FEATURE_COLS = ["age", "temp", "resp_rate", "spo2", "wbc", "crp"]


def main():
    if not DATA_PATH.is_file():
        raise FileNotFoundError(f"임상 데이터 CSV를 찾을 수 없습니다: {DATA_PATH}")

    print(f"[INFO] 임상 데이터 로드: {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)

    # 결측값 제거 (간단 버전)
    df = df.dropna(subset=FEATURE_COLS + ["label"])

    X = df[FEATURE_COLS]
    y = df["label"].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # 스케일러 + 로지스틱 회귀 파이프라인
    pipe = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=1000)),
        ]
    )

    print("[INFO] 임상 모델 학습 중...")
    pipe.fit(X_train, y_train)

    y_pred = pipe.predict(X_test)
    y_prob = pipe.predict_proba(X_test)[:, 1]

    print("\n=== Clinical Model Performance (임상 데이터만) ===")
    print(classification_report(y_test, y_pred))
    try:
        auc = roc_auc_score(y_test, y_prob)
        print(f"ROC-AUC: {auc:.4f}")
    except Exception:
        pass

    # 모델 + 피처 목록 저장
    joblib.dump({"model": pipe, "features": FEATURE_COLS}, MODEL_PATH)
    print(f"\n[INFO] 임상 모델 저장 완료: {MODEL_PATH}")


if __name__ == "__main__":
    main()
