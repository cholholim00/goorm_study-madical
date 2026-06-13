# grad_cam_xray.py
from pathlib import Path
import sys

import numpy as np
import tensorflow as tf
from PIL import Image
import matplotlib.cm as cm

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "models" / "xray_mobilenetv2_best.h5"

# Grad-CAM 결과 저장 폴더
REPORT_DIR = BASE_DIR / "reports" / "gradcam"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

IMG_SIZE = (160, 160)


def load_cam_model():
    """
    저장된 전체 모델에서
    - mobilenetv2_1.00_160 (feature extractor)
    - global_average_pooling2d, dropout, dense (head)
    를 꺼내서 Grad-CAM용 cam_model를 새로 만든다.
    outputs = [conv_feature_map, prediction]
    """
    if not MODEL_PATH.is_file():
        raise FileNotFoundError(f"X-ray 모델을 찾을 수 없습니다: {MODEL_PATH}")

    print(f"[INFO] 전체 모델 로드: {MODEL_PATH}")
    full_model = tf.keras.models.load_model(MODEL_PATH.as_posix(), compile=False)
    full_model.trainable = False

    # 서브모델 및 헤드 레이어 추출
    base_model = full_model.get_layer("mobilenetv2_1.00_160")
    gap_layer = full_model.get_layer("global_average_pooling2d")
    drop_layer = full_model.get_layer("dropout")
    dense_layer = full_model.get_layer("dense")

    # Grad-CAM용 그래프 재구성
    inputs = base_model.input                    # (None, 160, 160, 3)
    conv_outputs = base_model.output            # 마지막 conv feature map (5x5x1280)
    x = gap_layer(conv_outputs)
    x = drop_layer(x)
    preds = dense_layer(x)                       # (None, 1) 폐렴 확률

    cam_model = tf.keras.Model(inputs=inputs, outputs=[conv_outputs, preds])
    print("[INFO] Grad-CAM용 cam_model 구성 완료")
    return cam_model


def preprocess_image(img_path: Path):
    # 원본은 overlay용, 리사이즈 이미지는 모델 입력용
    img = Image.open(img_path).convert("RGB")
    img_resized = img.resize(IMG_SIZE)
    x = np.array(img_resized, dtype=np.float32) / 255.0
    x = np.expand_dims(x, axis=0)
    return img, x  # (원본 PIL 이미지, 입력 텐서)


def make_grad_cam_heatmap(cam_model, img_array):
    """
    cam_model: 입력 → [conv_feature_map, preds] 를 내놓는 모델
    img_array: (1, H, W, 3)
    """
    with tf.GradientTape() as tape:
        conv_outputs, predictions = cam_model(img_array)
        # 이진 분류이므로 preds[:, 0] (폐렴 확률)
        pred = predictions[:, 0]

    # conv feature map에 대한 gradient
    grads = tape.gradient(pred, conv_outputs)

    # 채널별 평균 → 중요도 weight
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))  # (C,)

    conv_outputs = conv_outputs[0]  # (H, W, C)
    # 채널 방향으로 가중합
    heatmap = conv_outputs @ pooled_grads[..., tf.newaxis]  # (H, W, 1)
    heatmap = tf.squeeze(heatmap)  # (H, W)

    # ReLU + 정규화
    heatmap = tf.maximum(heatmap, 0) / (tf.reduce_max(heatmap) + 1e-8)
    return heatmap.numpy(), float(pred.numpy()[0])


def save_overlay(original_img: Image.Image, heatmap, out_path: Path, alpha: float = 0.4):
    """
    원본 이미지 + heatmap 색깔 입혀서 합성 후 저장
    """
    # 0~1 → 0~255
    heatmap = np.uint8(255 * heatmap)
    heatmap_img = Image.fromarray(heatmap).resize(original_img.size)

    # 컬러맵 적용 (jet)
    heatmap_color = cm.get_cmap("jet")(np.array(heatmap_img) / 255.0)
    heatmap_color = np.uint8(heatmap_color * 255)
    heatmap_color = Image.fromarray(heatmap_color[..., :3])

    # 원본과 섞기
    overlay = Image.blend(original_img.convert("RGB"), heatmap_color, alpha=alpha)
    overlay.save(out_path)
    print(f"[INFO] Grad-CAM 이미지 저장: {out_path}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python grad_cam_xray.py <image_path>")
        sys.exit(1)

    img_path = Path(sys.argv[1])
    if not img_path.is_file():
        print(f"이미지 파일을 찾을 수 없습니다: {img_path}")
        sys.exit(1)

    cam_model = load_cam_model()
    original_img, x = preprocess_image(img_path)

    heatmap, prob = make_grad_cam_heatmap(cam_model, x)
    label = "PNEUMONIA" if prob >= 0.5 else "NORMAL"
    print(f"[INFO] P(neumonia) = {prob:.3f} → {label}")

    # reports/gradcam/ 아래에 저장 (원본 파일명 + _gradcam.png)
    out_name = f"{img_path.stem}_gradcam.png"
    out_path = REPORT_DIR / out_name
    save_overlay(original_img, heatmap, out_path)


if __name__ == "__main__":
    main()
