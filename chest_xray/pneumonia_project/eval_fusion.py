# eval_fusion.py
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import tensorflow as tf
from PIL import Image
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
)

BASE_DIR = Path(__file__).resolve().parent
FUSION_DATA_PATH = BASE_DIR / "data" / "fusion_data.csv"
XRAY_MODEL_PATH = BASE_DIR / "models" / "xray_mobilenetv2_best.h5"
CLIN_MODEL_PATH = BASE_DIR / "models" / "clinical_model.pkl"

IMG_SIZE = (160, 160)
ALPHA = 0.6  # p_final = 0.6 * p_xray + 0.4 * p_clinical

def load_xray_model():
    print(f"[INFO] X-ray 모델 로드: {XRAY_MODEL_PATH}")
    model = tf.keras.models.load_model(XRAY_MODEL_PATH.as_posix(), compile=False)
    return model

def load_clinical_model():
    print(f"[INFO] 임상 모델 로드: {CLIN_MODEL_PATH}")
    saved = joblib.load(CLIN_MODEL_PATH)
    model = saved["model"]
    features = saved.get("features", ["age", "temp", "resp_rate", "spo2", "wbc", "crp"])
    return model, features

def predict_xray_prob(model, img_path: Path) -> float:
    if not img_path.is_file():
        raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {img_path}")
    img = Image.open(img_path).convert("RGB")
    img = img.resize(IMG_SIZE)
    x = np.array(img, dtype=np.float32) / 255.0
    x = np.expand_dims(x, axis=0)
    prob = float(model.predict(x)[0][0])
    return prob

def main():
    if not FUSION_DATA_PATH.is_file():
        raise FileNotFoundError(f"fusion_data.csv를 찾을 수 없습니다: {FUSION_DATA_PATH}")

    print(f"[INFO] fusion_data: {FUSION_DATA_PATH}")
    df = pd.read_csv(FUSION_DATA_PATH)

    if "label" not in df.columns:
        raise ValueError("fusion_data.csv 안에 'label' 컬럼이 필요합니다 (0/1).")
    if "image_path" not in df.columns:
        raise ValueError("fusion_data.csv 안에 'image_path' 컬럼(이미지 경로)이 필요합니다.")

    xray_model = load_xray_model()
    clin_model, features = load_clinical_model()

    y_true = []
    p_xray_list = []
    p_clin_list = []
    p_final_list = []

    for idx, row in df.iterrows():
        try:
            # 이미지 경로 처리 (상대경로 → 절대경로)
            img_path = Path(row["image_path"])
            if not img_path.is_absolute():
                img_path = BASE_DIR / img_path

            p_x = predict_xray_prob(xray_model, img_path)

            clin_values = np.array([[row[f] for f in features]], dtype=float)
            if hasattr(clin_model, "predict_proba"):
                p_c = float(clin_model.predict_proba(clin_values)[0][1])
            else:
                p_c = float(clin_model.predict(clin_values)[0])

            p_final = ALPHA * p_x + (1.0 - ALPHA) * p_c

            y_true.append(int(row["label"]))
            p_xray_list.append(p_x)
            p_clin_list.append(p_c)
            p_final_list.append(p_final)

        except Exception as e:
            print(f"[WARN] row {idx} 처리 중 오류: {repr(e)}")
            continue

    y_true = np.array(y_true)
    p_xray = np.array(p_xray_list)
    p_clin = np.array(p_clin_list)
    p_final = np.array(p_final_list)

    y_pred_x = (p_xray >= 0.5).astype(int)
    y_pred_c = (p_clin >= 0.5).astype(int)
    y_pred_f = (p_final >= 0.5).astype(int)

    def metrics(y, y_prob, y_pred, name: str):
        acc = accuracy_score(y, y_pred)
        prec = precision_score(y, y_pred)
        rec = recall_score(y, y_pred)
        f1 = f1_score(y, y_pred)
        try:
            auc = roc_auc_score(y, y_prob)
        except Exception:
            auc = None

        print(f"\n===== {name} =====")
        print(f"Accuracy : {acc:.4f}")
        print(f"Precision: {prec:.4f}")
        print(f"Recall   : {rec:.4f}")
        print(f"F1-score : {f1:.4f}")
        if auc is not None:
            print(f"ROC-AUC  : {auc:.4f}")

        return acc, rec, f1, auc

    mx = metrics(y_true, p_xray, y_pred_x, "X-ray Only")
    mc = metrics(y_true, p_clin, y_pred_c, "Clinical Only")
    mf = metrics(y_true, p_final, y_pred_f, "Fusion (0.6*X + 0.4*C)")

    print("\n요약 (Accuracy / Recall / F1 / AUC):")
    print("Model         | Acc    | Recall | F1     | AUC")
    print("--------------+--------+--------+--------+------")
    def fmt(name, m):
        acc, rec, f1, auc = m
        auc_str = f"{auc:.4f}" if auc is not None else "N/A"
        print(f"{name:<13} | {acc:0.4f} | {rec:0.4f} | {f1:0.4f} | {auc_str}")

    fmt("X-ray", mx)
    fmt("Clinical", mc)
    fmt("Fusion", mf)


if __name__ == "__main__":
    main()
