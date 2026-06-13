import os
import argparse
from pathlib import Path

import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing import image

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "models" / "xray_mobilenetv2_best.h5"
IMG_SIZE = (160, 160)


def load_model():
    if not MODEL_PATH.is_file():
        raise FileNotFoundError(f"모델 파일을 찾을 수 없습니다: {MODEL_PATH}")

    print(f"[INFO] 모델 로드 중: {MODEL_PATH}")
    model = tf.keras.models.load_model(MODEL_PATH.as_posix(), compile=False)
    print("[INFO] 모델 로드 완료")
    return model


def predict_single(model, img_path: str):
    if not os.path.isfile(img_path):
        raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {img_path}")

    print(f"[INFO] 이미지 로드 중: {img_path}")
    img = image.load_img(img_path, target_size=IMG_SIZE)
    x = image.img_to_array(img) / 255.0
    x = np.expand_dims(x, axis=0)

    print("[INFO] 예측 수행 중...")
    prob = float(model.predict(x)[0][0])
    return prob


def main():
    parser = argparse.ArgumentParser(description="폐렴 X-ray 예측 스크립트")
    parser.add_argument(
        "-i",
        "--image",
        required=True,
        help="예측할 X-ray 이미지 경로 (예: chest_xray\\test\\NORMAL\\xxx.jpeg)",
    )
    args = parser.parse_args()

    model = load_model()
    prob = predict_single(model, args.image)

    print(f"\nP(neumonia) = {prob:.3f}")
    if prob >= 0.5:
        print("→ 모델 기준: 폐렴(양성)에 더 가깝게 판단")
    else:
        print("→ 모델 기준: 정상(음성)에 더 가깝게 판단")


if __name__ == "__main__":
    main()
