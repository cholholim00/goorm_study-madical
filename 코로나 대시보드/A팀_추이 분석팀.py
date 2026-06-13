import pandas as pd
import plotly.graph_objects as go
import os

base_path = os.path.dirname(os.path.abspath(__file__))
full_path = os.path.join(base_path, 'data', 'cleaned_covid_data.csv')

df = pd.read_csv(full_path)
df['date'] = pd.to_datetime(df['date'])

fig = go.Figure()
fig.add_trace(go.Scatter(x=df['date'], y=df['total'], name='신규 확진자', line=dict(color='royalblue')))
fig.add_trace(go.Scatter(x=df['date'], y=df['death'], name='신규 사망자', line=dict(color='red'), yaxis='y2'))

fig.update_layout(
    title='대한민국 코로나19 확진자 및 사망자 추이',
    xaxis_title='날짜',
    yaxis_title='확진자 수',
    yaxis2=dict(title='사망자 수', overlaying='y', side='right'),
    template='plotly_white',
    hovermode='x unified'
)

print("✅ A팀 분석 그래프 생성 완료!")
fig.show()