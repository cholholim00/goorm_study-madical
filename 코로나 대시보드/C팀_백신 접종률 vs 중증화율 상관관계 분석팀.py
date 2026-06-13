import pandas as pd
import plotly.graph_objects as go
import os

# 1. 통합 데이터 불러오기
base_path = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(base_path, 'data', 'cleaned_covid_data.csv')

if not os.path.exists(file_path):
    print("❌ 통합 데이터 파일이 없습니다. 전처리 코드를 먼저 실행하세요!")
    exit()

df = pd.read_csv(file_path)
df['date'] = pd.to_datetime(df['date'])

# 2. 분석할 백신 데이터 컬럼 찾기
# 우리가 방금 만든 'accumulated_vaccine_count'(누적 접종) 컬럼을 우선 찾습니다.
target_vac_col = 'accumulated_vaccine_count'

if target_vac_col not in df.columns:
    # 만약 영어 이름이 없으면 한글 이름이나 다른 키워드로 다시 찾기
    candidates = [c for c in df.columns if '누적' in c or 'vaccine' in c or '접종' in c]
    if candidates:
        target_vac_col = candidates[-1] # 가장 마지막 후보 선택
    else:
        print("⚠️ 백신 데이터 컬럼을 찾을 수 없습니다. 데이터 통합이 제대로 되었는지 확인해주세요.")
        exit()

print(f"💉 분석 대상 백신 데이터: {target_vac_col}")

# 3. [핵심 그래프] 이중축 차트 그리기
# 왼쪽 축: 일일 사망자 (막대) / 오른쪽 축: 누적 접종자 (선)
fig = go.Figure()

# (1) 사망자 막대 그래프 (빨간색)
fig.add_trace(go.Bar(
    x=df['date'], 
    y=df['death'], 
    name='일일 사망자',
    marker_color='red',
    opacity=0.4
))

# (2) 백신 접종 선 그래프 (초록색, 오른쪽 축 사용)
fig.add_trace(go.Scatter(
    x=df['date'], 
    y=df[target_vac_col], 
    name='누적 백신 접종 수',
    line=dict(color='green', width=4),
    yaxis='y2' # 오른쪽 Y축 지정
))

# 레이아웃 설정 (축 제목 등)
fig.update_layout(
    title='💉 백신 접종 증가(초록선)와 사망자 발생(빨간막대)의 관계',
    xaxis=dict(title='날짜'),
    yaxis=dict(title='일일 사망자 수 (명)', side='left'),
    yaxis2=dict(
        title='누적 백신 접종 수 (명)', 
        overlaying='y', 
        side='right', 
        showgrid=False
    ),
    template='plotly_white',
    hovermode='x unified',
    legend=dict(x=0.01, y=0.99, bgcolor='rgba(255,255,255,0.5)')
)

print("✅ C팀 분석 그래프 생성 완료!")
fig.show()