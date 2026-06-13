import pandas as pd
import numpy as np
import os
from scipy import stats

# 1. 파일 경로 설정
input_path = 'dataset/heart.csv'
output_path = 'dataset/heart_cleaned.csv'

# 데이터 폴더가 있는지 확인 (없으면 생성)
if not os.path.exists('dataset'):
    os.makedirs('dataset')

# 2. 데이터 로드
try:
    df = pd.read_csv(input_path)
    print(f"데이터 로드 성공: {input_path}")
except FileNotFoundError:
    print(f"오류: {input_path} 파일을 찾을 수 없습니다. 경로를 확인해주세요.")
    exit()

# 3. 중복 데이터 제거
# 중복된 행이 많을 경우 모델의 성능이 왜곡될 수 있으므로 제거합니다.
df_cleaned = df.drop_duplicates().copy()

# 4. 범주형 데이터의 이상치(잘못된 값) 처리
# 'ca'(주요 혈관 수: 0-3), 'thal'(결함 여부: 1-3) 범위를 벗어난 값을 최빈값으로 대체
df_cleaned.loc[df_cleaned['ca'] == 4, 'ca'] = df_cleaned['ca'].mode()[0]
df_cleaned.loc[df_cleaned['thal'] == 0, 'thal'] = df_cleaned['thal'].mode()[0]

# 5. 수치형 데이터 이상치(Outlier) 제거
# 혈압, 콜레스테롤 등에서 통계적으로 너무 튀는 값(Z-score > 3) 제거
continuous_cols = ['trestbps', 'chol', 'thalach', 'oldpeak']
z_scores = np.abs(stats.zscore(df_cleaned[continuous_cols]))
df_cleaned = df_cleaned[(z_scores < 3).all(axis=1)]

# 6. 정제된 데이터 저장
df_cleaned = df_cleaned.reset_index(drop=True)
df_cleaned.to_csv(output_path, index=False)

print("-" * 30)
print(f"전처리 완료!")
print(f"원본 데이터 수: {len(df)}")
print(f"정제 후 데이터 수: {len(df_cleaned)}")
print(f"저장 경로: {output_path}")
print("-" * 30)

# 전처리 결과 상위 5개 확인
print(df_cleaned.head())