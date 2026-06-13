# # CH06 (데이터 그리기 (시각화 - Seaborn))
# **No.18 Seaborn 라이브러리:** Matplotlib보다 훨씬 예쁘고 쉬운 도구입니다.
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# 한글 깨짐 방지 설정 (Windows 기준)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 데이터 불러오기
df = pd.read_csv('patient_data.csv')

# **No.19 산점도 (`scatterplot`):** 나이가 많을수록 혈압도 높을까? (상관관계 확인)
plt.figure(figsize=(8,5))
sns.scatterplot(x='나이', y='혈압', data=df, hue='진단명', s=100)
plt.title('나이에 따른 혈압 분포')
plt.show()

# **No.20 히스토그램 (`histplot`):** 우리 병원 환자들은 주로 몇 살일까? (분포 확인)
plt.figure(figsize=(8,5))
sns.histplot(df['나이'], bins = 10, kde=True, color='skyblue')
plt.title('환자 나이대 분포')
plt.show()

# **No.21 박스플롯 (`boxplot`):** 남성과 여성의 당뇨 수치 차이 비교하기.
plt.figure(figsize=(8,5))
sns.scatterplot(x='진단명', y='혈당', data=df, hue='진단명', palette='Set2', legend=False)
plt.title('진단 결과별 혈당 수치 비교')
plt.show()

# 그래프 읽는 법 (팀원들과 공유하세요!)
# 산점도(Scatter): 점들이 오른쪽 위로 올라가는 모양이면 "나이가 들수록 혈압도 높다"는 양의 상관관계가 있다고 해석합니다.
#
# 히스토그램(Hist): 봉우리가 어디에 있는지 보고 "우리 병원엔 50대 환자가 제일 많네!"라고 주요 타겟을 파악합니다.
#
# 박스플롯(Box): 상자의 높이를 보고 "당뇨군 환자들이 확실히 정상군보다 혈당 수치 범위가 높고 넓구나"라고 그룹 간 차이를 분석합니다.

# - **No.22 "데이터 보고서 그리기"**
# - Kaggle의 타이타닉(Titanic) 혹은 당뇨병 데이터를 받아, **"나이에 따른 생존율"** 혹은 **"당뇨병 유무에 따른 혈당 차이"**를 그래프 하나로 그려서 캡처해 공유하세요.
# 타이타닉 데이터 불러오기
titanic = sns.load_dataset('titanic')

# 2. 그래프 그리기 (나이대별 생존 여부)
plt.figure(figsize=(10, 6))
sns.histplot(data=df, x='나이', hue='혈당', multiple='stack', kde=True)

plt.title('타이타닉: 나이대별 생존자 vs 사망자 분포')
plt.xlabel('나이')
plt.ylabel('인원 수')
plt.show()

