import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import streamlit as st
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import cv2
from PIL import Image

# ==========================================
# 1. 모델 구조 정의 (학습 때와 똑같아야 함)
# ==========================================
class UNet(nn.Module):
    def __init__(self):
        super(UNet, self).__init__()
        self.enc1 = self.conv_block(3, 64)
        self.enc2 = self.conv_block(64, 128)
        self.enc3 = self.conv_block(128, 256)
        self.enc4 = self.conv_block(256, 512)
        self.bottleneck = self.conv_block(512, 1024)
        self.up4 = self.up_conv(1024, 512)
        self.dec4 = self.conv_block(1024, 512)
        self.up3 = self.up_conv(512, 256)
        self.dec3 = self.conv_block(512, 256)
        self.up2 = self.up_conv(256, 128)
        self.dec2 = self.conv_block(256, 128)
        self.up1 = self.up_conv(128, 64)
        self.dec1 = self.conv_block(128, 64)
        self.final = nn.Conv2d(64, 1, kernel_size=1)

    def conv_block(self, in_c, out_c):
        return nn.Sequential(
            nn.Conv2d(in_c, out_c, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_c),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_c, out_c, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_c),
            nn.ReLU(inplace=True)
        )

    def up_conv(self, in_c, out_c):
        return nn.ConvTranspose2d(in_c, out_c, kernel_size=2, stride=2)

    def forward(self, x):
        e1 = self.enc1(x)
        p1 = F.max_pool2d(e1, 2)
        e2 = self.enc2(p1)
        p2 = F.max_pool2d(e2, 2)
        e3 = self.enc3(p2)
        p3 = F.max_pool2d(e3, 2)
        e4 = self.enc4(p3)
        p4 = F.max_pool2d(e4, 2)
        b = self.bottleneck(p4)
        d4 = self.up4(b)
        d4 = torch.cat((e4, d4), dim=1)
        d4 = self.dec4(d4)
        d3 = self.up3(d4)
        d3 = torch.cat((e3, d3), dim=1)
        d3 = self.dec3(d3)
        d2 = self.up2(d3)
        d2 = torch.cat((e2, d2), dim=1)
        d2 = self.dec2(d2)
        d1 = self.up1(d2)
        d1 = torch.cat((e1, d1), dim=1)
        d1 = self.dec1(d1)
        return self.final(d1)

# ==========================================
# 2. 모델 로드 함수 (캐싱 사용)
# ==========================================
@st.cache_resource
def load_model():
    model = UNet()
    # CPU로 로드 (어디서든 돌아가게)
    try:
        model.load_state_dict(torch.load('unet_brain_mri_local.pth', map_location=torch.device('cpu')))
    except:
        st.error("❌ 모델 파일(unet_brain_mri_local.pth)을 찾을 수 없습니다. 같은 폴더에 있는지 확인하세요!")
        return None
    model.eval()
    return model

# ==========================================
# 3. Streamlit UI 구성
# ==========================================
st.set_page_config(page_title="Brain Tumor AI", layout="wide")

st.title("🧠 뇌 종양 분석 AI (Brain MRI Segmentation)")
st.markdown("MRI 이미지를 업로드하면 **인공지능(U-Net)**이 종양 위치를 찾아냅니다.")

# 사이드바
st.sidebar.header("설정")
alpha = st.sidebar.slider("종양 표시 투명도", 0.0, 1.0, 0.4)

# 파일 업로드
uploaded_file = st.file_uploader("MRI 이미지 파일(.tif, .jpg, .png)을 선택하세요", type=["tif", "jpg", "png", "jpeg"])

if uploaded_file is not None:
    # 1. 이미지 읽기
    image = Image.open(uploaded_file).convert('RGB')
    img_array = np.array(image)
    
    # 2. 전처리 (Resize & Normalize)
    original_size = img_array.shape[:2] # 나중에 복원용
    img_resized = cv2.resize(img_array, (256, 256))
    img_tensor = img_resized / 255.0
    img_tensor = torch.from_numpy(img_tensor).permute(2, 0, 1).unsqueeze(0).float()

    # 3. 모델 예측
    model = load_model()
    if model:
        with torch.no_grad():
            pred = model(img_tensor)
            pred = torch.sigmoid(pred)
            pred = (pred > 0.5).float() # 0.5 이상이면 종양
            
        # 4. 결과 처리
        mask = pred.squeeze().cpu().numpy()
        mask = cv2.resize(mask, (original_size[1], original_size[0])) # 원본 크기로 복구

        # 5. 시각화 (원본 위에 빨간색 덮어씌우기)
        # 마스크가 있는 부분만 빨간색으로 칠함
        overlay = img_array.copy()
        overlay[mask == 1] = [255, 0, 0] # Red Color

        # 투명하게 합치기
        result_img = cv2.addWeighted(overlay, alpha, img_array, 1 - alpha, 0)

        # 6. 화면 출력
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("원본 MRI (Original)")
            st.image(img_array, use_container_width=True)
        
        with col2:
            st.subheader("AI 분석 결과 (Prediction)")
            st.image(result_img, use_container_width=True, caption="붉은색 영역이 AI가 찾은 종양입니다.")

        if mask.max() == 0:
            st.info("✅ 이 이미지에서는 종양이 발견되지 않았습니다.")
        else:
            st.warning("⚠️ 종양 의심 부위가 감지되었습니다.")