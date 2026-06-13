import pandas as pd
import os
import shutil
import openpyxl

# 1. 파일 경로 설정
base_path = os.path.dirname(os.path.abspath(__file__))
infection_file = os.path.join(base_path, 'data', 'cleaned_covid_data.csv')
vaccine_file = os.path.join(base_path, '질병관리청_코로나19 예방접종 통계 현황_20240805.csv')
temp_vac_excel = os.path.join(base_path, 'temp_vaccine_final_v5.xlsx')

def ultimate_vaccine_merge_v2():
    try:
        print("🚀 [최종 해결] 백신 데이터의 복잡한 구조를 뚫고 통합을 시작합니다...")

        if not os.path.exists(vaccine_file):
            print("❌ 에러: 백신 파일이 없습니다.")
            return

        # 1. 엑셀로 변환 및 로드
        shutil.copyfile(vaccine_file, temp_vac_excel)
        wb = openpyxl.load_workbook(temp_vac_excel, data_only=True)
        
        all_regions_df = pd.DataFrame()
        
        # 2. 수집 대상 시트 (지역명)
        regions = ['서울', '부산', '대구', '인천', '광주', '대전', '울산', '세종', 
                   '경기', '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주']
        
        valid_sheets = [s for s in wb.sheetnames if s in regions]
        print(f"📋 수집 대상 시트({len(valid_sheets)}개): {valid_sheets}")

        # 3. 데이터 추출
        for sheet_name in valid_sheets:
            # 5번째 줄(Index 4)부터 데이터가 시작됨 (헤더는 무시하고 위치로 접근)
            # 날짜는 1번 컬럼(B열)에 있음
            df_temp = pd.read_excel(temp_vac_excel, sheet_name=sheet_name, header=4, engine='openpyxl')
            
            # 컬럼 이름이 복잡하므로, 위치(Index)로 데이터 선택
            # 1번 컬럼: 날짜
            # 나머지 컬럼: 접종 데이터 (문자열 섞여있을 수 있음)
            
            # 날짜 컬럼 확보 (두 번째 컬럼)
            date_col_name = df_temp.columns[1] 
            df_temp = df_temp.rename(columns={date_col_name: 'date'})
            
            # 날짜 변환 (20210226.0 -> 2021-02-26)
            # 숫자를 문자로 바꾸고 .0 제거 후 날짜로 변환
            df_temp['date'] = df_temp['date'].astype(str).str.replace(r'\.0$', '', regex=True)
            df_temp['date'] = pd.to_datetime(df_temp['date'], format='%Y%m%d', errors='coerce')
            
            # 날짜가 없는 행 제거 (유효한 데이터만 남김)
            df_temp = df_temp.dropna(subset=['date'])
            
            # 백신 데이터 컬럼들 (날짜 컬럼 제외한 모든 숫자형 데이터)
            # 여기서는 단순히 '접종 건수'라고 가정하고 모든 컬럼을 다 합치기엔 너무 많으므로,
            # 주요 컬럼(예: 3번째 컬럼부터 끝까지)을 숫자로 변환
            data_cols = df_temp.columns[2:] # 0:NaN, 1:Date, 2~:Data
            
            # 숫자 변환
            for col in data_cols:
                # 컬럼명을 유니크하게 만들기 위해 임시로 변경할 수도 있지만,
                # 여기서는 값만 취합하므로 그냥 변환
                df_temp[col] = df_temp[col].astype(str).str.replace(',', '').str.replace(' ', '')
                df_temp[col] = pd.to_numeric(df_temp[col], errors='coerce').fillna(0).astype(int)
            
            # 날짜별 합계 (해당 지역의 하루 총 접종량)
            # 여기서는 상세 구분(1차, 2차 등)을 다 살리기보다, '일일 총 접종 건수'로 퉁쳐서 합산
            # 왜냐하면 헤더가 너무 복잡해서 매핑이 어렵기 때문
            df_temp['daily_vaccine_count'] = df_temp[data_cols].sum(axis=1)
            
            # 필요한 것만 남김
            df_subset = df_temp[['date', 'daily_vaccine_count']].copy()
            
            # 전체 데이터에 추가
            all_regions_df = pd.concat([all_regions_df, df_subset])

        # 4. 전국 합계 계산
        print("🔄 전국 백신 데이터 합산 중...")
        national_df = all_regions_df.groupby('date')['daily_vaccine_count'].sum().reset_index()
        
        # 누적 접종량 계산 (그래프를 예쁘게 그리기 위해)
        national_df['accumulated_vaccine_count'] = national_df['daily_vaccine_count'].cumsum()
        
        print(f"✅ 전국 데이터 생성 완료! ({len(national_df)}일치)")

        # 5. 기존 확진자 데이터와 병합
        if not os.path.exists(infection_file):
             print("❌ 확진자 파일이 없습니다.")
             return

        df_infection = pd.read_csv(infection_file)
        df_infection['date'] = pd.to_datetime(df_infection['date'])
        
        # 병합
        df_final = pd.merge(df_infection, national_df, on='date', how='left')
        df_final = df_final.fillna(0)
        
        # 정수형 변환
        num_cols = df_final.select_dtypes(include=['float']).columns
        for c in num_cols:
            df_final[c] = df_final[c].astype(int)

        # 저장
        df_final.to_csv(infection_file, index=False, encoding='utf-8-sig')
        
        if os.path.exists(temp_vac_excel):
            os.remove(temp_vac_excel)
            
        print("\n" + "="*50)
        print("🎉 [미션 컴플리트] 전국 백신 데이터 통합 완료!")
        print(f"📊 최종 데이터 크기: {len(df_final)}행")
        print(f"💉 추가된 컬럼: daily_vaccine_count, accumulated_vaccine_count")
        print("="*50)

    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    ultimate_vaccine_merge_v2()