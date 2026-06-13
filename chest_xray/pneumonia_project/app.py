import streamlit as st
import tensorflow as tf
import numpy as np
import pandas as pd
import joblib
import cv2
import matplotlib.cm as cm
from PIL import Image
from fpdf import FPDF
import tempfile
import datetime
import os

# -----------------------------------------------------------------------------
# 1. 설정 및 디자인 (Korean Medical Theme)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="MediFusion Pro | 지능형 폐렴 진단 솔루션",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    /* 폰트 및 기본 컬러 설정 */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Noto Sans KR', sans-serif;
    }
    .stApp { background-color: #1e1e1e; color: #f0f2f6; }
    
    /* 사이드바 스타일 */
    [data-testid="stSidebar"] { background-color: #2b2b2b; border-right: 1px solid #444; }
    
    /* 결과 카드 스타일 */
    .metric-card {
        background-color: #333; border: 1px solid #555;
        padding: 20px; border-radius: 10px; text-align: center;
        margin-bottom: 20px;
    }
    .result-text { font-size: 1.1rem; line-height: 1.6; color: #ddd; }
    .highlight-red { color: #ff6b6b; font-weight: bold; }
    .highlight-green { color: #51cf66; font-weight: bold; }
    
    /* 버튼 커스텀 */
    .stButton>button {
        background-color: #339af0; color: white; border: none;
        border-radius: 5px; height: 50px; font-size: 1rem; font-weight: bold;
    }
    .stButton>button:hover { background-color: #1c7ed6; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 한글 PDF 생성 클래스 (상세 리포트용)
# -----------------------------------------------------------------------------
class MedicalReportPDF(FPDF):
    def __init__(self):
        super().__init__()
        # 한글 폰트 등록 (프로젝트 폴더에 NanumGothic.ttf가 있어야 함)
        # 폰트가 없으면 기본 폰트(Arial) 사용 (한글 깨짐 방지용 try-except)
        self.font_ok = False
        try:
            self.add_font('Nanum', '', 'NanumGothic.ttf', uni=True)
            self.add_font('Nanum', 'B', 'NanumGothic.ttf', uni=True)
            self.font_ok = True
        except:
            pass

    def header(self):
        if self.font_ok:
            self.set_font('Nanum', 'B', 20)
        else:
            self.set_font('Arial', 'B', 20)
        
        self.cell(0, 10, 'AI 의료 영상 판독 결과지', 0, 1, 'C')
        self.ln(5)
        
        # 구분선
        self.set_line_width(0.5)
        self.line(10, 25, 200, 25)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        if self.font_ok:
            self.set_font('Nanum', '', 8)
        else:
            self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'MediFusion AI System | Page {self.page_no()}', 0, 0, 'C')

    def add_section_title(self, title):
        if self.font_ok:
            self.set_font('Nanum', 'B', 14)
        else:
            self.set_font('Arial', 'B', 14)
        self.set_fill_color(240, 240, 240)
        self.cell(0, 10, f"  {title}", 0, 1, 'L', fill=True)
        self.ln(2)

    def add_body_text(self, text):
        if self.font_ok:
            self.set_font('Nanum', '', 11)
        else:
            self.set_font('Arial', '', 11)
        self.multi_cell(0, 7, text)
        self.ln(3)

def generate_medical_text(age, temp, wbc, crp, xray_prob, final_prob):
    """
    입력된 데이터를 바탕으로 의사처럼 보이는 소견 텍스트 생성
    """
    findings = []
    
    # 1. 임상 소견
    clinical_notes = []
    if temp >= 37.5:
        clinical_notes.append(f"- 체온이 {temp}도로 발열 증세가 확인됩니다.")
    if wbc > 10000:
        clinical_notes.append(f"- 백혈구 수치(WBC)가 {wbc}로 상승하여 감염 반응이 의심됩니다.")
    if crp > 10.0:
        clinical_notes.append(f"- 염증 수치(CRP)가 {crp}mg/L로 기준치를 초과했습니다.")
    
    if not clinical_notes:
        findings.append("임상 활력 징후 및 혈액 검사상 특이 소견은 발견되지 않았습니다.")
    else:
        findings.append("임상 데이터 분석 결과:\n" + "\n".join(clinical_notes))

    # 2. 영상 소견
    if xray_prob < 0.3:
        findings.append(f"흉부 X-ray AI 분석 결과, 폐렴을 시사하는 불투명 음영은 관찰되지 않았습니다. (AI 확신도: {xray_prob*100:.1f}%)")
    elif xray_prob < 0.6:
        findings.append(f"흉부 X-ray 상 경미한 의심 영역이 탐지되었으나, 확정적이지 않습니다. (AI 확신도: {xray_prob*100:.1f}%)")
    else:
        findings.append(f"흉부 X-ray 상 폐렴과 유사한 고밀도 음영 패턴이 감지되었습니다. (AI 확신도: {xray_prob*100:.1f}%)")

    # 3. 종합 결론
    if final_prob >= 0.7:
        conclusion = "종합적으로 [고위험군]으로 분류됩니다. 폐렴의 가능성이 높으므로 전문의의 정밀 진단 및 추가 검사(CT 등)를 권고합니다."
    elif final_prob >= 0.4:
        conclusion = "종합적으로 [관찰 필요] 단계입니다. 임상 증상의 변화를 주기적으로 모니터링하시기 바랍니다."
    else:
        conclusion = "[정상 범위]로 판단됩니다. 현재 시점에서 폐렴을 의심할 만한 유의미한 증거는 부족합니다."

    return "\n\n".join(findings), conclusion

def create_korean_pdf(patient_info, xray_prob, clin_prob, final_prob, img_original, detailed_text, conclusion):
    pdf = MedicalReportPDF()
    pdf.add_page()
    
    # 폰트 체크
    if not pdf.font_ok:
        st.error("⚠️ 'NanumGothic.ttf' 파일이 없어 한글이 깨질 수 있습니다.")

    # 1. 환자 정보
    pdf.add_section_title("1. 환자 기본 정보 (Patient Info)")
    info_str = f"검사 일시: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    for k, v in patient_info.items():
        info_str += f"- {k}: {v}\n"
    pdf.add_body_text(info_str)

    # 2. 종합 분석 결과
    pdf.add_section_title("2. AI 종합 분석 (AI Analysis)")
    pdf.add_body_text(detailed_text)
    
    pdf.set_text_color(255, 0, 0) # 빨간색
    pdf.add_body_text(f"결론: {conclusion}")
    pdf.set_text_color(0, 0, 0) # 검은색 복귀

    # 3. 상세 수치
    pdf.add_section_title("3. 정량적 지표 (Metrics)")
    metrics = (
        f"Vision AI (X-ray) Score: {xray_prob*100:.1f}%\n"
        f"Clinical AI Score: {clin_prob*100:.1f}%\n"
        f"Fusion Risk Score: {final_prob*100:.1f}%"
    )
    pdf.add_body_text(metrics)

    # 4. 영상 첨부
    pdf.add_section_title("4. 분석 영상 (Analyzed Image)")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        img_original.save(tmp.name)
        # 이미지 크기 조정해서 넣기
        pdf.image(tmp.name, x=15, y=None, w=100)
    
    return pdf.output(dest='S').encode('latin-1')

# -----------------------------------------------------------------------------
# 3. 모델 로드 (경로 설정)
# -----------------------------------------------------------------------------
@st.cache_resource
def get_config():
    import pathlib
    BASE_DIR = pathlib.Path(__file__).resolve().parent
    return {
        "XRAY_MODEL": BASE_DIR / "models" / "xray_mobilenetv2_best.h5",
        "CLIN_MODEL": BASE_DIR / "models" / "clinical_model.pkl",
        "IMG_SIZE": (160, 160)
    }

CONFIG = get_config()

@st.cache_resource
def load_resources():
    resources = {}
    # X-ray 모델
    try:
        full_model = tf.keras.models.load_model(str(CONFIG["XRAY_MODEL"]), compile=False)
        full_model.trainable = False
        resources["xray_full"] = full_model
        
        # Grad-CAM 모델 재구성
        try:
            base_model = full_model.get_layer("mobilenetv2_1.00_160")
            gap_layer = full_model.get_layer("global_average_pooling2d")
            drop_layer = full_model.get_layer("dropout")
            dense_layer = full_model.get_layer("dense")
            inputs = base_model.input
            conv_outputs = base_model.output
            x = gap_layer(conv_outputs)
            x = drop_layer(x)
            preds = dense_layer(x)
            resources["cam_model"] = tf.keras.Model(inputs=inputs, outputs=[conv_outputs, preds])
            resources["gradcam_ok"] = True
        except:
            resources["gradcam_ok"] = False
    except Exception as e:
        st.error(f"X-ray 모델 로드 실패: {e}")
        return None

    # Clinical 모델
    try:
        saved = joblib.load(CONFIG["CLIN_MODEL"])
        resources["clin_model"] = saved["model"]
    except Exception as e:
        st.error(f"임상 모델 로드 실패: {e}")
        return None
    return resources

def make_gradcam_heatmap(cam_model, img_array):
    with tf.GradientTape() as tape:
        conv_outputs, predictions = cam_model(img_array)
        pred = predictions[:, 0]
    grads = tape.gradient(pred, conv_outputs)
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
    conv_outputs = conv_outputs[0]
    heatmap = conv_outputs @ pooled_grads[..., tf.newaxis]
    heatmap = tf.squeeze(heatmap)
    heatmap = tf.maximum(heatmap, 0) / (tf.reduce_max(heatmap) + 1e-8)
    return heatmap.numpy(), float(pred.numpy()[0])

def overlay_heatmap(original_img, heatmap, alpha=0.4):
    heatmap = np.uint8(255 * heatmap)
    heatmap_img = Image.fromarray(heatmap).resize(original_img.size)
    jet = cm.get_cmap("jet")
    heatmap_color = jet(np.array(heatmap_img) / 255.0)
    heatmap_color = np.uint8(heatmap_color * 255)
    heatmap_color = Image.fromarray(heatmap_color[..., :3])
    return Image.blend(original_img.convert("RGB"), heatmap_color, alpha=alpha)

# -----------------------------------------------------------------------------
# 4. 메인 UI (한글화 및 정밀 조정 기능 추가)
# -----------------------------------------------------------------------------
st.sidebar.title("🩺 MediFusion 설정")

# --- 1. 민감도 조절 (정상 폐 구분 문제 해결용) ---
st.sidebar.subheader("⚙️ AI 민감도 설정")
threshold = st.sidebar.slider(
    "판정 기준값 (Threshold)", 
    0.0, 1.0, 0.6, 0.05,
    help="이 값보다 확률이 높아야 '폐렴'으로 판정합니다. 정상 폐를 폐렴으로 잡으면 이 값을 올리세요."
)

st.sidebar.divider()

# --- 2. 임상 데이터 입력 ---
st.sidebar.subheader("📋 환자 데이터")
age = st.sidebar.number_input("나이 (세)", 0, 120, 65)
temp = st.sidebar.number_input("체온 (℃)", 30.0, 45.0, 36.5, format="%.1f")
resp_rate = st.sidebar.number_input("호흡수 (회/분)", 10, 60, 20)
spo2 = st.sidebar.number_input("산소포화도 (%)", 50, 100, 98)
wbc = st.sidebar.number_input("백혈구 (WBC)", 0, 50000, 8000)
crp = st.sidebar.number_input("염증수치 (CRP)", 0.0, 300.0, 5.0, format="%.1f")

# --- 메인 화면 ---
st.title("🩺 AI 기반 폐렴 정밀 진단 시스템")
st.markdown("X-ray 영상 분석과 임상 데이터를 결합하여 **상세 진단 리포트**를 제공합니다.")

uploaded_file = st.file_uploader("흉부 X-ray 이미지를 업로드하세요 (JPG, PNG)", type=["jpg", "png", "jpeg"])

if uploaded_file:
    resources = load_resources()
    if resources:
        # 이미지 처리
        img_original = Image.open(uploaded_file).convert("RGB")
        img_resized = img_original.resize(CONFIG["IMG_SIZE"])
        x_input = np.array(img_resized, dtype=np.float32) / 255.0
        x_input = np.expand_dims(x_input, axis=0)
        
        # 1. AI 영상 분석
        if resources["gradcam_ok"]:
            heatmap, raw_xray_prob = make_gradcam_heatmap(resources["cam_model"], x_input)
            gradcam_img = overlay_heatmap(img_original, heatmap)
        else:
            raw_xray_prob = resources["xray_full"].predict(x_input)[0][0]
            gradcam_img = img_original
            st.warning("히트맵 생성 불가 (기본 예측 수행)")

        # 2. 임상 데이터 분석
        clin_input = np.array([[age, temp, resp_rate, spo2, wbc, crp]], dtype=float)
        p_clinical = resources["clin_model"].predict_proba(clin_input)[0][1]
        
        # 3. Fusion (결합)
        ALPHA = 0.6
        p_final = (ALPHA * raw_xray_prob) + ((1 - ALPHA) * p_clinical)

        # 4. 결과 판정 (Threshold 적용)
        is_pneumonia = p_final >= threshold
        
        if is_pneumonia:
            if p_final >= 0.8:
                status = "심각 (High Risk)"
                color_cls = "highlight-red"
            else:
                status = "주의 (Medium Risk)"
                color_cls = "highlight-red" # 주황색 대신 빨강 통일
        else:
            status = "정상 (Normal)"
            color_cls = "highlight-green"

        # --- 화면 표시 레이아웃 ---
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("🖼️ 영상 분석 결과")
            tab1, tab2 = st.tabs(["🔥 AI 분석 (히트맵)", "원본 영상"])
            with tab1: st.image(gradcam_img, use_column_width=True, caption="붉은 영역: AI가 의심하는 부위")
            with tab2: st.image(img_original, use_column_width=True)

        with col2:
            st.subheader("📊 진단 요약")
            
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size:1.2rem; color:#aaa;">최종 진단 결과</div>
                <div style="font-size:2.5rem; margin:10px 0;" class="{color_cls}">{status}</div>
                <div style="font-size:1rem;">통합 위험도 확률: <b>{p_final*100:.1f}%</b></div>
            </div>
            """, unsafe_allow_html=True)
            
            st.write("**세부 분석:**")
            st.write(f"- 🫁 **X-ray AI 확신도:** {raw_xray_prob*100:.1f}%")
            st.write(f"- 🧪 **임상 데이터 위험도:** {p_clinical*100:.1f}%")
            st.caption(f"ℹ️ 현재 민감도 설정(Threshold): {threshold}")
            
            # 소견 생성
            detailed_txt, conclusion = generate_medical_text(age, temp, wbc, crp, raw_xray_prob, p_final)
            
            with st.expander("📝 자동 생성된 의학적 소견 보기", expanded=True):
                st.write(detailed_txt)
                st.write(f"**[종합 결론]** {conclusion}")

            # PDF 다운로드
            st.divider()
            patient_info = {"나이": f"{age}세", "체온": f"{temp}도", "WBC": str(int(wbc)), "CRP": str(crp)}
            pdf_bytes = create_korean_pdf(patient_info, raw_xray_prob, p_clinical, p_final, img_original, detailed_txt, conclusion)
            
            st.download_button(
                label="📄 상세 리포트 다운로드 (PDF)",
                data=pdf_bytes,
                file_name="medical_report_kr.pdf",
                mime="application/pdf"
            )

else:
    st.info("좌측 사이드바에서 임상 데이터를 설정하고, X-ray 이미지를 업로드해주세요.")