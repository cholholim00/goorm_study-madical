# CH05 (망가진 데이터 고치기 (전처리 & 파생변수))
import pandas as pd
import numpy as np

# df라는 변수에 데이터를 담아줍니다.
df = pd.DataFrame({
    '이름': ['환자1', '환자2', '환자3'],
    '혈압': [120, np.nan, 130],
    'Height': [170, 180, 165],
    'Weight': [70, 80, 60]
})

# **No.15 결측치 처리 (`isnull`, `fillna`):** 비어있는 혈압 데이터를 '평균값'으로 채우거나, 데이터가 없는 행을 지우기(`dropna`).
# 1. 혈압 열의 빈칸을 평균값으로 채우기
df["혈압"] = df["혈압"].fillna(df["혈압"].mean())
print("\n1. 혈압 열의 빈칸을 평균값으로 채우기")
print(df)

# 2. 데이터가 하나라도 없는 행은 삭제하기
df_clean = df.dropna()
print("\n2. 데이터가 하나라도 없는 행은 삭제하기")
print(df_clean)

# **No.16 파생변수 만들기:** 키(Height)와 몸무게(Weight) 컬럼을 이용해 **'BMI'** 컬럼을 새로 만들어 표에 붙이기.
# BMI 열 추가하기
df["BMI"] = df["Weight"] / (df["Height"] / 100)**2
print("\n--- BMI 계산 완료 ---")
print(df)

# - **No.17 팀 미션: "BMI 자동 계산기"**
# - 키(cm)와 몸무게(kg) 데이터가 있는 표를 만들고, 코드로 계산하여 맨 오른쪽 열에 `BMI` 수치를 자동으로 채워 넣으세요. (결측치가 있다면 0으로 채우세요!)
# 1. 가상의 키/몸무게 데이터 생성 (결측치 일부 포함)
data = {
    '이름': ['강서준', '김도윤', '이현우', '박지민', '최성민'],
    'Height': [175, 182, np.nan, 160, 170], # 이현우 환자 키 누락
    'Weight': [70, 85, 62, np.nan, 75]      # 박지민 환자 몸무게 누락
}
df_bmi = pd.DataFrame(data)

# 2. 결측치 처리: 0으로 채우기 (미션 조건)
# 실제 의료 데이터라면 평균값을 쓰지만, 이번 미션은 0으로 채워봅니다.
df_bmi = df_bmi.fillna(0)

# 3. BMI 자동 계산 및 맨 오른쪽 열에 추가
# 키가 0인 경우(결측치) 계산 오류를 방지하기 위해 아주 작은 값을 더하거나 조건문을 쓸 수 있지만,
# 여기서는 기본 공식을 적용합니다.
df_bmi['BMI'] = df_bmi['Weight'] / (df_bmi['Height'] / 100)**2

# 4. 결과 출력 (소수점 둘째자리까지 반올림)
df_bmi['BMI'] = df_bmi['BMI'].round(2)

# 키나 몸무게가 0이었던 데이터는 BMI가 0이나 inf(무한대)로 나올 수 있으므로 최종 정리
df_bmi = df_bmi.replace([np.inf, -np.inf], 0).fillna(0)

print("\n--- BMI 자동 계산 결과 ---")
print(df_bmi)