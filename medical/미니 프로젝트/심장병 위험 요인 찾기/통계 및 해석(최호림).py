import pandas as pd
import numpy as np
from scipy import stats

# 1. 전처리된 데이터 로드 (팀 공통 데이터)
try:
    df = pd.read_csv('dataset/heart_cleaned.csv')
except:
    df = pd.read_csv('heart_cleaned.csv') # 경로 예외 처리

# ---------------------------------------------------------
# [인사이트 1] 상관계수 분석 (임동영 님 그래프 해석용)
# ---------------------------------------------------------
corrations = df.corr()['target'].sort_values(ascending=False)
top_positive = corrations.index[1] # target 제외 1위 (보통 cp)
top_negative = corrations.index[-1] # 음의 상관관계 1위 (보통 thalach)

# ---------------------------------------------------------
# [인사이트 2] 그룹별 통계 차이 분석 (전재영/정유진 님 그래프 해석용)
# ---------------------------------------------------------
# 심장병 유무(target)에 따른 주요 지표 평균값 차이 계산
summary_stats = df.groupby('target')[['thalach', 'oldpeak', 'age', 'trestbps']].mean()

# ---------------------------------------------------------
# [인사이트 3] 가설 검정 (김주희 & 사용자 담당 영역)
# ---------------------------------------------------------
# "심장병이 있는 집단과 없는 집단의 최대 심박수(thalach) 차이는 통계적으로 유의미한가?"
group0 = df[df['target'] == 0]['thalach']
group1 = df[df['target'] == 1]['thalach']
t_stat, p_val = stats.ttest_ind(group0, group1)

# ---------------------------------------------------------
# 📋 최종 통계 보고서 출력
# ---------------------------------------------------------
print("="*50)
print("     심장병 위험 요인 통계 분석 결과 보고서")
print("="*50)

print(f"\n1. 가장 강력한 양의 상관관계: {top_positive} ({corrations[top_positive]:.3f})")
print(f"   => 해석: {top_positive} 수치가 높을수록 심장병 확률이 증가합니다.")

print(f"\n2. 가장 강력한 음의 상관관계: {top_negative} ({corrations[top_negative]:.3f})")
print(f"   => 해석: {top_negative} 수치가 낮을수록 심장병 위험이 높아집니다.")

print("\n3. 집단별 주요 지표 평균 차이:")
print(summary_stats)

print("\n4. 통계적 유의성 검정 (T-test):")
print(f"   - 최대 심박수(thalach) p-value: {p_val:.10f}")
if p_val < 0.05:
    print("   => 결론: 심장병 유무에 따른 심박수 차이는 통계적으로 매우 유의미함.")
else:
    print("   => 결론: 통계적으로 유의미한 차이가 발견되지 않음.")

print("="*50)