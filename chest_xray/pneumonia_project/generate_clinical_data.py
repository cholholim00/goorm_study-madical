from pathlib import Path
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "clinical_data.csv"

np.random.seed(42)

N = 200  # 샘플 개수 (원하면 숫자 늘려도 됨)

ages = np.random.randint(18, 90, size=N)              # 나이
temps = np.random.normal(loc=37.2, scale=0.7, size=N) # 체온
resp_rates = np.random.normal(loc=18, scale=4, size=N)  # 호흡수
spo2s = np.random.normal(loc=96, scale=3, size=N)       # 산소포화도
wbcs = np.random.normal(loc=8000, scale=2500, size=N)   # WBC
crps = np.abs(np.random.normal(loc=5, scale=4, size=N)) # CRP (양수로)

# 간단한 규칙 기반으로 label 생성 (1 = 위험, 0 = 저위험)
labels = []
for age, temp, rr, spo2, wbc, crp in zip(ages, temps, resp_rates, spo2s, wbcs, crps):
    risk_score = 0

    if age >= 65:
        risk_score += 1
    if temp >= 38.0:
        risk_score += 1
    if rr >= 24:
        risk_score += 1
    if spo2 <= 92:
        risk_score += 2
    if wbc >= 12000 or wbc <= 4000:
        risk_score += 1
    if crp >= 10:
        risk_score += 1

    # 위험 점수 3 이상 → 1(입원/중등도 이상), 아니면 0
    label = 1 if risk_score >= 3 else 0
    labels.append(label)

df = pd.DataFrame(
    {
        "age": ages,
        "temp": temps.round(1),
        "resp_rate": resp_rates.round(0),
        "spo2": spo2s.round(0),
        "wbc": wbcs.round(0),
        "crp": crps.round(1),
        "label": labels,
    }
)

print(df.head())
df.to_csv(DATA_PATH, index=False, encoding="utf-8-sig")
print(f"[INFO] 임상 샘플 데이터 저장 완료: {DATA_PATH} (rows={len(df)})")
