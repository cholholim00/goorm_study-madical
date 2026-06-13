import pandas as pd
import numpy as np
import plotly.express as px

# 1) 데이터 로드
df = pd.read_csv("/Users/goorm/desktop/goorm/python_start/plotly/practice/heart_cleaned.csv")  # 경로 필요하면 수정
target = "target"

# 2) 연속형/범주형 나누기
continuous_cols = ["age", "trestbps", "chol", "thalach", "oldpeak"]
categorical_cols = [c for c in df.columns if c not in continuous_cols + [target]]

# -----------------------------
# A) 연속형 연관도: |corr|
# -----------------------------
cont_scores = (
    df[continuous_cols]
    .corrwith(df[target])
    .abs()
    .rename("score")
    .reset_index()
    .rename(columns={"index": "feature"})
)
cont_scores["kind"] = "continuous(|corr|)"

# -----------------------------
# B) 범주형 연관도(대체 지표): 카테고리별 target=1 비율의 표준편차(std)
# - std가 크다 = 어떤 카테고리는 위험 높고, 어떤 카테고리는 낮다 = 관련이 더 커 보인다
# -----------------------------
cat_rows = []
for c in categorical_cols:
    rates = df.groupby(c)[target].mean()   # 각 카테고리의 심장병(1) 비율
    score = rates.std()                    # 비율이 얼마나 갈리는지
    cat_rows.append((c, score))

cat_scores = pd.DataFrame(cat_rows, columns=["feature", "score"])
cat_scores["kind"] = "categorical(rate_std)"

# -----------------------------
# C) 합쳐서 랭킹 그래프
# -----------------------------
scores = pd.concat([cont_scores, cat_scores], ignore_index=True)
scores = scores.sort_values("score", ascending=False)

fig1 = px.bar(
    scores,
    x="score",
    y="feature",
    color="kind",
    orientation="h",
    title="심장병(target)과 변수 연관도 랭킹",
    hover_data={"score": ":.3f"}
)
fig1.update_layout(yaxis={"categoryorder": "total ascending"})
fig1.show()

# -----------------------------
# D) 1등 변수 상세 그래프
# -----------------------------
top_feature = scores.iloc[0]["feature"]
top_kind = scores.iloc[0]["kind"]

if top_kind.startswith("continuous"):
    fig2 = px.box(
        df,
        x=target,
        y=top_feature,
        points="all",
        title=f"Top 변수 상세: {top_feature} (target=0 vs 1 분포)"
    )
    fig2.show()
else:
    rate = (
        df.groupby(top_feature)[target]
        .mean()
        .reset_index()
        .rename(columns={target: "target_rate"})
        .sort_values("target_rate", ascending=False)
    )
    fig2 = px.bar(
        rate,
        x=top_feature,
        y="target_rate",
        text="target_rate",
        title=f"Top 변수 상세: {top_feature} 카테고리별 심장병 비율(target=1)"
    )
    fig2.update_traces(texttemplate="%{text:.2f}", textposition="outside")
    fig2.update_layout(yaxis_tickformat=".0%")
    fig2.show()