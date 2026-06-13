# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import plotly.express as px

# 데이터 불러오기
df = pd.read_csv("heart_cleaned.csv")
target = "target"

# 연속형 / 범주형 변수 구분
continuous_cols = ["age", "trestbps", "chol", "thalach", "oldpeak"]
categorical_cols = [c for c in df.columns if c not in continuous_cols + [target]]

# 연속형 변수 점수 (|상관계수|)
cont_scores = (
    df[continuous_cols]
    .corrwith(df[target])
    .abs()
    .rename("score")
    .reset_index()
    .rename(columns={"index": "feature"})
)
cont_scores["type"] = "continuous"

# 범주형 변수 점수
# 카테고리별 target=1 비율 차이
cat_rows = []

for col in categorical_cols:
    rates = df.groupby(col)[target].mean()
    score = rates.std()  # 집단 간 차이 크기
    cat_rows.append((col, score))

cat_scores = pd.DataFrame(cat_rows, columns=["feature", "score"])
cat_scores["type"] = "categorical"

# 점수 합치기
scores = pd.concat([cont_scores, cat_scores], ignore_index=True)
scores = scores.sort_values("score", ascending=False)

print("\n통계적으로 분리 계산한 위험 요인 순위")
print(scores)

# 시각화 (Dot plot)
fig = px.scatter(
    scores,
    x="score",
    y="feature",
    color="type",
    size="score",
    title="심장병 위험 요인 중요도"
)

fig.update_layout(
    yaxis={"categoryorder": "total ascending"},
    xaxis_title="관련성 점수",
    yaxis_title="변수"
)

fig.show()