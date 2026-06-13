'''
## [미니 프로젝트] 심장병 위험 요인 찾기
**No28. 데이터셋 준비 -** **Heart Disease UCI**
**No29. 상관관계 분석 (`heatmap`):** 심장병과 가장 관련 깊은 변수는 무엇일까? (콜레스테롤? 최대 심박수?)
- No.30. 역할 분담하여 최종 발표자료 만들기
    - 팀원 B(3명): 시각화 담당 (각 그래프 1개씩 그리기)
'''

# ========== No.29 상관관계 분석: 컬럼 선택 이유 ==========
# 대상 컬럼: target을 제외한 모든 숫자형 컬럼 (age, sex, cp, trestbps, chol, fbs, restecg, thalach, exang, oldpeak, slope, ca, thal)
# 이유: 심장병(target)과의 관계를 "모든 후보 변수"에 대해 공정하게 비교하려면, 일부만 쓰지 않고
#       상관계수가 계산 가능한 모든 컬럼을 포함하는 것이 맞음.
#       시각화에서 절댓값 정렬로 "가장 관련 깊은 변수"가 자동으로 상위에 오도록 함.

# ========== No.29 그래프 선택 이유 (Heatmap) ==========
# - 막대 차트·dot plot 외에 상관관계를 잘 표현하는 방식으로 히트맵을 사용함.
# - target은 축에 넣지 않고, "target과의 상관계수" 한 행(1×13)만 그려서
#   심장병과 각 변수의 관련 강도(양/음, 크기)를 색으로 비교함. 컬럼 선택 이유와 일치.
# - plotly.express의 px.imshow 사용 (seaborn/matplotlib 미사용).

import pandas as pd
import plotly.express as px
import plotly.subplots as sp
import os

data_folder_path = os.path.join(os.path.dirname(__file__), 'data')
df = pd.read_csv(os.path.join(data_folder_path, 'heart_cleaned.csv'))

# 상관계수 행렬 계산 (모든 숫자형 컬럼 간 피어슨 상관계수)
corr = df.corr()

# target과의 상관계수만 추출, 절댓값 기준 정렬(관련이 깊은 순). 축에는 target 미포함.
target_corr = corr['target'].drop('target')
target_corr_sorted = target_corr.reindex(target_corr.abs().sort_values(ascending=False).index)

# x축 라벨 한글 매핑 (Heart Disease UCI 컬럼명 → 한글)
col_ko = {
    'age': '나이',
    'sex': '성별',
    'cp': '흉통 유형',
    'trestbps': '안정 시 혈압',
    'chol': '콜레스테롤',
    'fbs': '공복 혈당',
    'restecg': '안정 시 심전도',
    'thalach': '최대 심박수',
    'exang': '운동 유발 협심증',
    'oldpeak': 'ST 하강',
    'slope': 'ST 기울기',
    'ca': '주요 혈관 수',
    'thal': '탈라세미아',
}
x_labels_ko = [col_ko.get(name, name) for name in target_corr_sorted.index.tolist()]

# 1×13 히트맵: x축에 변수 13개만, y축은 "target과의 상관계수" 한 행 (target은 축에 표시하지 않음)
corr_row = target_corr_sorted.values.reshape(1, -1)
fig = px.imshow(
    corr_row,
    x=x_labels_ko,
    y=['target과의 상관계수'],
    color_continuous_scale='RdBu_r',
    aspect='auto',
    zmin=-1,
    zmax=1,
    labels=dict(color='상관계수', x='변수'),
    title='심장병(target)과의 상관계수 — 관련이 깊은 변수 순',
)
fig.update_layout(xaxis_tickangle=-45)


# 세 차트를 한 화면에서 동시 확인: 서브플롯으로 결합 후 한 번에 표시
combined = sp.make_subplots(
    rows=3,
    cols=1,
    subplot_titles=(
        '심장병(target)과의 상관계수 — 관련이 깊은 변수 순',
    ),
    vertical_spacing=0.10,
    row_heights=[0.35, 0.35, 0.30],
)
for trace in fig.data:
    combined.add_trace(trace, row=1, col=1)
combined.update_layout(height=1200, showlegend=True)
combined.update_xaxes(tickangle=-45, row=1, col=1)
combined.update_xaxes(tickangle=-45, row=2, col=1)
combined.show()
