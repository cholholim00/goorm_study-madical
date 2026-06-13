import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os

# -----------------------------------------------------------------------------
# [Step 4: UI/UX 최적화] 페이지 설정 & 기깔나는 커스텀 스타일
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="코로나19 종합 상황실",
    page_icon="🦠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🎨 [디자인 업그레이드] 팀별 전용 컬러 CSS 적용
# A팀(추이): 파란색 / B팀(지역): 초록색 / C팀(백신): 주황색
st.markdown("""
    <style>
    /* 전체 탭 컨테이너 스타일 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 60px;
        border-radius: 10px 10px 0 0;
        font-weight: bold;
        font-size: 1.1rem;
        border: none;
        transition: all 0.3s;
    }

    /* 📈 A팀 탭 (파랑) */
    .stTabs [data-baseweb="tab"]:nth-of-type(1) {
        background-color: #E3F2FD; /* 평소: 연한 파랑 */
        color: #1565C0;
    }
    .stTabs [data-baseweb="tab"]:nth-of-type(1)[aria-selected="true"] {
        background-color: #2196F3; /* 선택됨: 진한 파랑 */
        color: white;
        box-shadow: 0px -4px 10px rgba(33, 150, 243, 0.3);
    }

    /* 🗺️ B팀 탭 (초록) */
    .stTabs [data-baseweb="tab"]:nth-of-type(2) {
        background-color: #E8F5E9; /* 평소: 연한 초록 */
        color: #2E7D32;
    }
    .stTabs [data-baseweb="tab"]:nth-of-type(2)[aria-selected="true"] {
        background-color: #4CAF50; /* 선택됨: 진한 초록 */
        color: white;
        box-shadow: 0px -4px 10px rgba(76, 175, 80, 0.3);
    }

    /* 💉 C팀 탭 (주황/빨강) */
    .stTabs [data-baseweb="tab"]:nth-of-type(3) {
        background-color: #FFF3E0; /* 평소: 연한 주황 */
        color: #EF6C00;
    }
    .stTabs [data-baseweb="tab"]:nth-of-type(3)[aria-selected="true"] {
        background-color: #FF9800; /* 선택됨: 진한 주황 */
        color: white;
        box-shadow: 0px -4px 10px rgba(255, 152, 0, 0.3);
    }
    
    /* 배경 및 폰트 미세 조정 */
    .block-container {
        padding-top: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# [Step 3: 데이터 통합] 데이터 로드 함수
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    base_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_path, 'data', 'cleaned_covid_data.csv')
    
    if not os.path.exists(file_path):
        return None
    
    df = pd.read_csv(file_path)
    df['date'] = pd.to_datetime(df['date'])
    return df

df = load_data()

# 데이터 파일이 없을 경우 예외 처리
if df is None:
    st.error("🚨 데이터 파일이 없습니다! 'project_reset.py'를 먼저 실행하여 데이터를 복구해주세요.")
    st.stop()

# -----------------------------------------------------------------------------
# [Step 3: 레이아웃 설계] 사이드바 (필터 기능 구현)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("🎛️ 컨트롤 패널")
    
    # 1. 기간 설정 필터
    st.subheader("📅 분석 기간 설정")
    min_date = df['date'].min()
    max_date = df['date'].max()
    
    start_date, end_date = st.date_input(
        "날짜 범위 선택",
        [min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )
    
    st.markdown("---")
    
    # 2. 지역 선택 필터 (B팀용)
    st.subheader("🗺️ 관심 지역 선택")
    # 지역 컬럼 자동 추출 (기본 컬럼 제외)
    exclude_cols = ['date', 'total', 'domestic', 'overseas', 'death', 'daily_vaccine_count', 'accumulated_vaccine_count']
    all_regions = [c for c in df.columns if c not in exclude_cols and '접종' not in c]
    
    selected_regions = st.multiselect(
        "지역을 선택하세요 (기본: 전체)",
        all_regions,
        default=all_regions  # 기본값: 전체 선택
    )
    
    st.info(f"📊 총 {len(df)}일간의 데이터를 분석합니다.")

# 데이터 필터링 적용
mask = (df['date'] >= pd.to_datetime(start_date)) & (df['date'] <= pd.to_datetime(end_date))
filtered_df = df.loc[mask]

# -----------------------------------------------------------------------------
# [Main] 메인 대시보드 화면 구성
# -----------------------------------------------------------------------------
st.title("🦠 코로나19 데이터 분석 종합 대시보드")
st.markdown(f"**기간:** {start_date} ~ {end_date}")

# 핵심 지표 (Metrics) - 디자인 통일성 유지
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("총 확진자 수", f"{int(filtered_df['total'].sum()):,}명", delta="A팀 분석", delta_color="normal")
with col2:
    st.metric("총 사망자 수", f"{int(filtered_df['death'].sum()):,}명", delta="사망자 추이", delta_color="inverse")
with col3:
    if 'accumulated_vaccine_count' in filtered_df.columns:
        last_vac = filtered_df.iloc[-1]['accumulated_vaccine_count']
        st.metric("누적 백신 접종", f"{int(last_vac):,}건", delta="C팀 분석")

st.markdown("---")

# 탭 구성 (각 팀의 결과물 통합)
# 이모지를 넣어서 더 직관적으로 표현
tab1, tab2, tab3 = st.tabs(["📈 A팀: 종합 추이", "🗺️ B팀: 지역별 현황", "💉 C팀: 백신 효과"])

# --- [A팀] 확진자 vs 사망자 추이 ---
with tab1:
    st.subheader("📊 국내 코로나19 확진 및 사망 추이")
    
    fig_a = go.Figure()
    fig_a.add_trace(go.Scatter(x=filtered_df['date'], y=filtered_df['total'], name='신규 확진자', line=dict(color='#2196F3', width=2)))
    fig_a.add_trace(go.Scatter(x=filtered_df['date'], y=filtered_df['death'], name='신규 사망자', line=dict(color='#D32F2F', width=2), yaxis='y2'))
    
    fig_a.update_layout(
        xaxis=dict(title='날짜'),
        yaxis=dict(title='확진자 수', side='left', showgrid=False),
        yaxis2=dict(title='사망자 수', overlaying='y', side='right', showgrid=False),
        legend=dict(x=0.01, y=0.99),
        template='plotly_white',
        hovermode='x unified',
        height=500
    )
    st.plotly_chart(fig_a, use_container_width=True)

# --- [B팀] 지역별 발생 현황 ---
with tab2:
    st.subheader("🗺️ 지역별 확진자 발생 비교")
    
    if selected_regions:
        latest_row = df.iloc[-1]
        region_data = pd.DataFrame({
            'Region': selected_regions,
            'Count': [latest_row[r] for r in selected_regions]
        }).sort_values('Count', ascending=False)
        
        # B팀 테마색(초록 계열) 적용
        fig_b = px.bar(region_data, x='Region', y='Count', color='Count',
                       title=f"지역별 신규 확진자 ({latest_row['date'].date()} 기준)",
                       text_auto='.2s',
                       color_continuous_scale='Greens') # Greens 컬러맵 사용
        
        fig_b.update_layout(xaxis_title="지역", yaxis_title="확진자 수", template='plotly_white', height=500)
        st.plotly_chart(fig_b, use_container_width=True)
    else:
        st.warning("⚠️ 사이드바에서 지역을 하나 이상 선택해주세요.")

# --- [C팀] 백신 효과 분석 ---
with tab3:
    st.subheader("💉 백신 접종과 사망률의 상관관계 분석")
    
    vac_col = 'accumulated_vaccine_count'
    if vac_col in filtered_df.columns:
        fig_c = go.Figure()
        
        # 사망자 (막대)
        fig_c.add_trace(go.Bar(
            x=filtered_df['date'], y=filtered_df['death'], 
            name='일일 사망자', marker_color='#EF5350', opacity=0.4
        ))
        
        # 백신 접종 (선) - C팀 테마색(주황) 적용
        fig_c.add_trace(go.Scatter(
            x=filtered_df['date'], y=filtered_df[vac_col], 
            name='누적 백신 접종', 
            line=dict(color='#FF9800', width=4), # 주황색 라인
            yaxis='y2'
        ))
        
        fig_c.update_layout(
            title='백신 접종(주황선) 증가에 따른 사망자(빨간막대) 변화',
            xaxis=dict(title='날짜'),
            yaxis=dict(title='일일 사망자 수', side='left'),
            yaxis2=dict(title='누적 접종 수', overlaying='y', side='right', showgrid=False),
            template='plotly_white',
            hovermode='x unified',
            legend=dict(x=0.01, y=0.99),
            height=500
        )
        st.plotly_chart(fig_c, use_container_width=True)
        
        with st.expander("💡 데이터 해석 보기"):
            st.markdown("""
            - **분석 결과:** 백신 접종(주황색 선)이 급격히 증가하는 시점 이후, 확진자가 늘더라도 사망자(빨간색 막대)의 증가폭이 억제되는 경향을 확인할 수 있습니다.
            - **결론:** 백신 접종은 코로나19의 중증화 및 사망 위험을 낮추는 데 기여했을 가능성이 높습니다.
            """)
    else:
        st.warning("⚠️ 백신 데이터를 시각화할 수 없습니다. 데이터 통합 상태를 확인하세요.")