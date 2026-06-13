import pandas as pd
import plotly.express as px
import os

base_path = os.path.dirname(os.path.abspath(__file__))
full_path = os.path.join(base_path, 'data', 'cleaned_covid_data.csv')

def run_b_team():
    try:
        df = pd.read_csv(full_path)
        # 1. 가장 최신 날짜 데이터 가져오기
        latest_date = df['date'].max()
        latest_df = df[df['date'] == latest_date].iloc[0]

        # 2. 분석할 지역 리스트
        regions = ['서울', '부산', '대구', '인천', '광주', '대전', '울산', '경기', '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주']
        
        region_values = []
        region_names = []
        for r in regions:
            if r in df.columns:
                region_values.append(latest_df[r])
                region_names.append(r)

        # 3. 막대 그래프 그리기
        fig = px.bar(x=region_names, y=region_values, 
                     title=f"지역별 신규 확진 현황 (기준일: {latest_date})",
                     labels={'x': '지역', 'y': '확진자 수'},
                     color=region_values, 
                     color_continuous_scale='Reds')

        fig.update_layout(xaxis={'categoryorder':'total descending'}, template='plotly_white')
        fig.show()
        print(f"✅ {latest_date} B팀 분석 그래프 생성 완료!")

    except Exception as e:
        print(f"❌ B팀 에러 발생: {e}")

if __name__ == "__main__":
    run_b_team()