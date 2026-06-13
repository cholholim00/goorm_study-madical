import random

# No.4 함수 (나만의 의료 프로토콜 만들어보기) - 당뇨병 위험군 자동 분류 시스템
def diagnose_diabetes(name, sugar_level):
    if sugar_level < 100:
        status = "정상"
    elif 100 <= sugar_level <= 125:
        status = "당뇨 전단계 (내당능 장애)"
    else:
        status = "당뇨 의심 (정밀 검사 필요)"

    return f"[{name} 환자] 혈당: {sugar_level}mg/dL -> 판정: {status}"

# No.5 라이브러리 (남이 만든 의료기기 가져와보자!)
# 70에서 150 사이의 임의의 혈당 수치 생성
test_sugar = random.randint(70, 150)
print(diagnose_diabetes("테스트용", test_sugar))

# No.6 "자동 건강검진 판정기"
# 1. 환자 데이터 리스트 (이름, 혈당수치)
patient_list = [
    ("강환자", 95),
    ("이당뇨", 142),
    ("박주의", 115),
    ("최정상", 88)
]

print("=== 당뇨 스크리닝 일괄 결과 ===")

# 2. 반복문을 이용한 자동 판정
for name, sugar in patient_list:
    report = diagnose_diabetes(name, sugar)
    print(report)