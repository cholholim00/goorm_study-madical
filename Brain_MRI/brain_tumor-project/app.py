import streamlit as st
import torch
import torch.nn as nn
import numpy as np
import matplotlib.pyplot as plt
import os
from fpdf import FPDF
import base64
from datetime import datetime
import plotly.graph_objects as go

# === 1. 모델 설계도 ===
# === 1. 모델 설계도 (코랩에서 학습할 때 썼던 오리지널 U-Net) ===
class DoubleConv(nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.double_conv = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )
    def forward(self, x):
        return self.double_conv(x)

class UNet(nn.Module):
    def __init__(self, n_channels=1, n_classes=1):
        super(UNet, self).__init__()
        self.inc = DoubleConv(n_channels, 64)
        self.down1 = DoubleConv(64, 128)
        self.down2 = DoubleConv(128, 256)
        self.down3 = DoubleConv(256, 512)
        
        self.pool = nn.MaxPool2d(2)
        self.bot = DoubleConv(512, 1024)
        
        self.up1 = nn.ConvTranspose2d(1024, 512, kernel_size=2, stride=2)
        self.dec1 = DoubleConv(1024, 512)
        self.up2 = nn.ConvTranspose2d(512, 256, kernel_size=2, stride=2)
        self.dec2 = DoubleConv(512, 256)
        self.up3 = nn.ConvTranspose2d(256, 128, kernel_size=2, stride=2)
        self.dec3 = DoubleConv(256, 128)
        self.up4 = nn.ConvTranspose2d(128, 64, kernel_size=2, stride=2)
        self.dec4 = DoubleConv(128, 64)
        
        self.outc = nn.Conv2d(64, n_classes, kernel_size=1)

    def forward(self, x):
        x1 = self.inc(x)
        x2 = self.down1(self.pool(x1))
        x3 = self.down2(self.pool(x2))
        x4 = self.down3(self.pool(x3))
        x5 = self.bot(self.pool(x4))
        
        x = self.up1(x5)
        x = torch.cat([x4, x], dim=1) 
        x = self.dec1(x)
        x = self.up2(x)
        x = torch.cat([x3, x], dim=1)
        x = self.dec2(x)
        x = self.up3(x)
        x = torch.cat([x2, x], dim=1)
        x = self.dec3(x)
        x = self.up4(x)
        x = torch.cat([x1, x], dim=1)
        x = self.dec4(x)
        
        return self.outc(x)

# === 2. 기본 설정 및 모델 로드 ===
st.set_page_config(page_title="NeuroScan AI", page_icon="🧠", layout="wide")

st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 5px; background-color: #FF4B4B; color: white; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def load_model():
    # 내 컴퓨터에 GPU가 없어도 알아서 CPU로 돌아가게 설정합니다.
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = UNet().to(device)
    
    # 모델 파일이 app.py와 같은 폴더에 있다고 가정합니다.
    model_path = 'unet_brain_tumor.pth'
    
    if os.path.exists(model_path):
        # CPU 환경에서도 문제없이 불러오도록 map_location 추가
        model.load_state_dict(torch.load(model_path, map_location=device))
        model.eval()
        return model, device
    return None, None

model, device = load_model()

# === 3. 사이드바 (환자 정보) ===
with st.sidebar:
    st.title("🏥 NeuroScan AI")
    st.markdown("---")
    st.subheader("환자 정보 입력")
    p_id = st.text_input("환자 ID", "PT-2024-001")
    p_name = st.text_input("성명", "홍길동")
    p_age = st.number_input("나이", 20, 100, 45)
    p_gender = st.selectbox("성별", ["남성", "여성"])
    st.markdown("---")
    if model is None:
        st.error("🚨 'unet_brain_tumor.pth' 파일이 폴더에 없습니다! 구글 드라이브에서 다운받아 넣어주세요.")
    else:
        st.info("💡 MRI(Flair) 슬라이스 이미지를 업로드하여 정밀 분석을 시작하세요.")

# === 4. 메인 화면 ===
st.title("🧠 뇌 종양 AI 정밀 진단 대시보드")
st.markdown("##### Artificial Intelligence Brain Tumor Segmentation System")

col1, col2 = st.columns([1, 2])

with col1:
    uploaded_file = st.file_uploader("MRI 파일 업로드 (.npy)", type=['npy'])

if uploaded_file and model:
    # 데이터 전처리
    img_array = np.load(uploaded_file)
    input_tensor = torch.from_numpy(img_array).float().unsqueeze(0).unsqueeze(0).to(device)
    
    # AI 예측
    with torch.no_grad():
        output = model(input_tensor)
        pred_prob = torch.sigmoid(output).cpu().numpy()[0][0]
        pred_mask = (pred_prob > 0.5).astype(np.float32)

    # === 5. 탭 구성 (분석 화면) ===
    tab1, tab2, tab3 = st.tabs(["🔍 시각적 분석", "📊 정량적 리포트", "📑 PDF 다운로드"])

    # [탭 1] 시각적 분석
    with tab1:
        col_a, col_b = st.columns(2)
        with col_a:
            st.image(img_array, caption="원본 MRI", use_column_width=True, clamp=True)
        with col_b:
            fig = go.Figure()
            fig.add_trace(go.Heatmap(z=img_array, colorscale='Gray', showscale=False))
            heatmap_data = np.where(pred_mask > 0, 1, None)
            fig.add_trace(go.Heatmap(z=heatmap_data, colorscale='Reds', showscale=False, opacity=0.5))
            fig.update_layout(title="AI 예측 결과 (Overlay)", xaxis_showticklabels=False, yaxis_showticklabels=False, margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig, use_container_width=True)

    # [탭 2] 정량적 분석
    with tab2:
        tumor_pixels = np.sum(pred_mask)
        tumor_area_cm2 = (tumor_pixels * 1 * 1) / 100 # 1px = 1mm^2 가정
        
        st.subheader("🔬 종양 분석 결과")
        m1, m2, m3 = st.columns(3)
        m1.metric("탐지 여부", "양성 (Positive)" if tumor_pixels > 0 else "음성 (Negative)", delta_color="inverse")
        m2.metric("종양 픽셀 수", f"{int(tumor_pixels)} px")
        m3.metric("추정 면적", f"{tumor_area_cm2:.2f} cm²")
        
        if tumor_pixels > 0:
            st.markdown("---")
            st.markdown("**AI 확신도 분포 (Confidence Score)**")
            fig_hist = go.Figure(data=[go.Histogram(x=pred_prob[pred_mask==1], nbinsx=20)])
            fig_hist.update_layout(height=300, xaxis_title="확률 (0.5 ~ 1.0)", yaxis_title="픽셀 수")
            st.plotly_chart(fig_hist, use_container_width=True)

    # [탭 3] PDF 다운로드
    with tab3:
        st.subheader("📑 진단 보고서 생성")
        if st.button("진단 보고서 PDF 생성"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(200, 10, txt="NeuroScan AI - Medical Report", ln=True, align='C')
            pdf.set_font("Arial", size=12)
            pdf.ln(10)
            pdf.cell(200, 10, txt=f"Patient ID: {p_id}", ln=True)
            pdf.cell(200, 10, txt=f"Name: {p_name} ({p_gender}, Age {p_age})", ln=True)
            pdf.cell(200, 10, txt=f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
            pdf.ln(10)
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(200, 10, txt="Diagnosis Result", ln=True)
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt=f"AI Prediction: {'Tumor Detected' if tumor_pixels > 0 else 'No Tumor Detected'}", ln=True)
            pdf.cell(200, 10, txt=f"Tumor Area: {tumor_area_cm2:.2f} cm2", ln=True)
            
            plt.imsave("temp_mask.png", pred_mask, cmap='Reds')
            pdf.image("temp_mask.png", x=10, y=100, w=100)
            
            html = pdf.output(dest='S').encode('latin-1')
            b64 = base64.b64encode(html).decode()
            href = f'<a href="data:application/octet-stream;base64,{b64}" download="Medical_Report_{p_id}.pdf">📥 PDF 보고서 다운로드 클릭</a>'
            st.markdown(href, unsafe_allow_html=True)
else:
    if model is not None:
        st.info("👈 왼쪽 화면에서 MRI 파일을 업로드해주세요.")