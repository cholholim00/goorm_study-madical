# clinical_feature_importance.py
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.inspection import permutation_importance

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
REPORT_DIR = BASE_DIR / "reports"

MODEL_PATH = BASE_DIR / "models" / "clinical_model.pkl"
DATA_PATH = DATA_DIR / "clinical_data.csv"


def main():
    if not MODEL_PATH.is_file():
        raise FileNotFoundError(f"임상 모델 파일을 찾을 수 없습니다: {MODEL_PATH}")
    if not DATA_PATH.is_file():
        raise FileNotFoundError(f"임상 데이터 CSV를 찾을 수 없습니다: {DATA_PATH}")

    # 폴더 준비
    REPORT_DIR.mkdir(exist_ok=True)

    print(f"[INFO] clinical_model: {MODEL_PATH}")
    print(f"[INFO] clinical_data: {DATA_PATH}")
    print(f"[INFO] report dir   : {REPORT_DIR}")

    # 1) 모델 & 피처
    saved = joblib.load(MODEL_PATH)
    model = saved["model"]
    features = saved.get("features", ["age", "temp", "resp_rate", "spo2", "wbc", "crp"])
    print("[INFO] 사용 피처:", features)

    # 2) 데이터 로드
    df = pd.read_csv(DATA_PATH)

    if "label" not in df.columns:
        raise ValueError("clinical_data.csv 안에 'label' 컬럼이 필요합니다 (0/1).")

    df = df.dropna(subset=features + ["label"])

    X = df[features].values.astype(float)
    y = df["label"].values.astype(int)

    print(f"[INFO] 샘플 개수: {len(df)}")

    # 3) Permutation Importance
    print("[INFO] Permutation Importance 계산 중...")
    result = permutation_importance(
        model,
        X,
        y,
        n_repeats=20,
        random_state=42,
        n_jobs=-1,
    )

    importances_mean = result.importances_mean
    importances_std = result.importances_std

    df_imp = (
        pd.DataFrame(
            {
                "feature": features,
                "importance_mean": importances_mean,
                "importance_std": importances_std,
            }
        )
        .sort_values("importance_mean", ascending=False)
        .reset_index(drop=True)
    )

    print("\n===== Clinical Feature Importance (Permutation) =====")
    print(
        df_imp.to_string(
            index=False,
            float_format=lambda x: f"{x:0.4f}",
        )
    )

    # 🔹 CSV → data 폴더
    csv_path = DATA_DIR / "clinical_feature_importance.csv"
    df_imp.to_csv(csv_path, index=False)
    print(f"[INFO] 중요도 표 CSV 저장: {csv_path}")

    # 🔹 PNG → reports 폴더
    png_path = REPORT_DIR / "clinical_feature_importance.png"
    plt.figure(figsize=(6, 4))
    plt.bar(df_imp["feature"], df_imp["importance_mean"], yerr=df_imp["importance_std"])
    plt.title("Clinical Feature Importance (Permutation)")
    plt.xlabel("Feature")
    plt.ylabel("Importance (mean decrease in score)")
    plt.tight_layout()
    plt.savefig(png_path, dpi=150)
    print(f"[INFO] 중요도 그래프 PNG 저장: {png_path}")


if __name__ == "__main__":
    main()
