import os
from pathlib import Path

import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras import layers, models
from tensorflow.keras.callbacks import ModelCheckpoint

# ===== 경로 설정 =====
BASE_DIR = Path(__file__).resolve().parent
DATA_ROOT = BASE_DIR / "chest_xray"

# chest_xray/train/... 구조
if (DATA_ROOT / "train").is_dir():
    DATA_DIR = DATA_ROOT
# chest_xray/chest_xray_processed/train/... 구조
elif (DATA_ROOT / "chest_xray_processed" / "train").is_dir():
    DATA_DIR = DATA_ROOT / "chest_xray_processed"
else:
    raise FileNotFoundError(
        f"데이터 폴더를 찾을 수 없습니다.\n"
        f"기대하는 위치:\n"
        f" - {DATA_ROOT / 'train'}\n"
        f" - {DATA_ROOT / 'chest_xray_processed' / 'train'}"
    )

TRAIN_DIR = DATA_DIR / "train"
VAL_DIR = DATA_DIR / "val"
MODEL_DIR = BASE_DIR / "models"
MODEL_DIR.mkdir(exist_ok=True)

# ===== 학습 설정 =====
IMG_SIZE = (160, 160)
BATCH_SIZE = 8
EPOCHS = 3  # 처음에는 3 epoch만

# ===== 데이터 제너레이터 =====
train_datagen = ImageDataGenerator(
    rescale=1.0 / 255,
    rotation_range=10,
    width_shift_range=0.1,
    height_shift_range=0.1,
    zoom_range=0.1,
    horizontal_flip=True,
)
val_datagen = ImageDataGenerator(rescale=1.0 / 255)

train_gen = train_datagen.flow_from_directory(
    TRAIN_DIR,
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode="binary",
)

val_gen = val_datagen.flow_from_directory(
    VAL_DIR,
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode="binary",
)

print("Class indices:", train_gen.class_indices)

# ===== MobileNetV2 기반 모델 =====
base_model = MobileNetV2(
    input_shape=IMG_SIZE + (3,),
    include_top=False,
    weights="imagenet",  # 인터넷 필요 (처음 한 번만)
)
base_model.trainable = False  # 처음에는 동결

inputs = layers.Input(shape=IMG_SIZE + (3,))
x = base_model(inputs, training=False)
x = layers.GlobalAveragePooling2D()(x)
x = layers.Dropout(0.3)(x)
outputs = layers.Dense(1, activation="sigmoid")(x)

model = models.Model(inputs, outputs)

model.compile(
    optimizer=tf.keras.optimizers.Adam(1e-4),
    loss="binary_crossentropy",
    metrics=["accuracy"],
)

model.summary()

# ===== 체크포인트 =====
ckpt_path = MODEL_DIR / "xray_mobilenetv2_best.h5"
checkpoint = ModelCheckpoint(
    ckpt_path.as_posix(),
    monitor="val_accuracy",
    save_best_only=True,
    verbose=1,
)

# ===== 학습 실행 =====
history = model.fit(
    train_gen,
    epochs=EPOCHS,
    validation_data=val_gen,
    callbacks=[checkpoint],
)

print(f"Best model saved to: {ckpt_path}")
