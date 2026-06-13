# 판다스 소환하기
import pandas as pd
# 1. 환자 테이블을 준비해보기
data = {
    "이름": ["김철수", "이영희", "박민수", "최지혜", "정수진"],
    "나이": [45, 32, 58, 29, 62],
    "성별": ["남", "여", "남", "여", "여"],
    "혈당": [95, 88, 140, 79, 150]
}
# 2. 판다스 표(DataFrame)로 변환해보기
df = pd.DataFrame(data) # 직접 만들기
# 만약 파일이 있다면 이렇게 불러오기
# df = pd.read_csv("data.csv")
print(">>>>>>출력하기")
print(df)
print("====================")

print(">>>>>>데이터 구조,결측치 확인<<<<<<")
df.info()
print("====================")

print(">>>>>>통계 정보 한 방에 보기<<<<<<")
# df.describe() #(주피터용) .py에서는 print()를 붙여야한다.
print(df.describe())
print("====================")

print(">>>>>>고위험군 자동 필터링<<<<<<")
high_glucose = df[df["혈당"] >= 120]
print(">>>>>>출력")
print(high_glucose)