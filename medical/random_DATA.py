import pandas as pd
import numpy as np

# 1. 50명의 가상 데이터 생성을 위한 설정
np.random.seed(42)  # 실행할 때마다 결과가 같게 나오도록 고정 (팀원들과 결과 공유 시 유용)
num_patients = 50

# 2. 랜덤 데이터 생성
names = [f'환자_{i+1}' for i in range(num_patients)]
ages = np.random.randint(20, 80, size=num_patients)  # 20세~80세 사이
blood_pressures = np.random.randint(90, 160, size=num_patients)  # 90~160 사이
glucoses = np.random.randint(70, 200, size=num_patients)  # 70~200 사이

# 진단명은 혈당 수치에 따라 자동으로 부여 (간단한 로직)
diagnoses = []
for g in glucoses:
    if g >= 140:
        diagnoses.append('당뇨')
    elif g >= 110:
        diagnoses.append('주의')
    else:
        diagnoses.append('정상')

# 3. 데이터프레임 만들기
df_50 = pd.DataFrame({
    '이름': names,
    '나이': ages,
    '혈압': blood_pressures,
    '혈당': glucoses,
    '진단명': diagnoses
})

# 4. CSV 파일로 저장
df_50.to_csv('patient_data.csv', index=False, encoding='utf-8-sig')

print("데이터 생성 완료! 상위 5개 데이터를 확인합니다:")
print(df_50.head())