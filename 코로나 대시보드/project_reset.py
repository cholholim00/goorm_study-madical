import pandas as pd
import os
import shutil
import openpyxl

# 1. 파일 경로 설정
base_path = os.path.dirname(os.path.abspath(__file__))
output_file = os.path.join(base_path, 'data', 'cleaned_covid_data.csv')

# 원본 파일명 (확인 필수)
file_inf = '질병관리청_코로나19 확진자 발생현황(전수감시)_20230831.csv'
file_vac = '질병관리청_코로나19 예방접종 통계 현황_20240805.csv'

temp_inf = os.path.join(base_path, 'temp_inf_reset.xlsx')
temp_vac = os.path.join(base_path, 'temp_vac_reset.xlsx')

def reset_and_build_data():
    try:
        print("🚀 [프로젝트 초기화] 데이터를 처음부터 다시 깨끗하게 구축합니다...")
        
        # ---------------------------------------------------
        # [Step 1] 확진자/사망자/지역 데이터 처리 (A, B팀)
        # ---------------------------------------------------
        print("   -> 1단계: 확진자 및 사망자 데이터 추출 중...")
        path_inf = os.path.join(base_path, file_inf)
        if not os.path.exists(path_inf):
            print(f"❌ 오류: {file_inf} 파일이 없습니다.")
            return

        shutil.copyfile(path_inf, temp_inf)
        xl = pd.ExcelFile(temp_inf, engine='openpyxl')
        
        # 1-1. 사망자 데이터 (보통 첫 번째 시트)
        df_death = xl.parse(0, skiprows=4)
        df_death.columns = [str(c).strip() for c in df_death.columns]
        
        # '사망' 컬럼 찾기
        death_col = next((c for c in df_death.columns if '사망' in c), None)
        date_col = next((c for c in df_death.columns if '일자' in c), None)
        
        if death_col and date_col:
            df_death = df_death[[date_col, death_col]].rename(columns={date_col: 'date', death_col: 'death'})
            df_death['date'] = pd.to_datetime(df_death['date'], errors='coerce')
            df_death = df_death.dropna(subset=['date'])
        else:
            print("⚠️ 사망자 데이터를 찾을 수 없습니다.")
            df_death = pd.DataFrame(columns=['date', 'death'])

        # 1-2. 지역 데이터 (시트 순회)
        df_region = pd.DataFrame()
        for sheet in xl.sheet_names:
            temp = xl.parse(sheet, header=None)
            # '서울'이 있는 행 찾기
            header_idx = -1
            for idx, row in temp.iterrows():
                if any('서울' in str(x) for x in row.values):
                    header_idx = idx
                    break
            if header_idx != -1:
                df_region = xl.parse(sheet, header=header_idx)
                break
        
        if not df_region.empty:
            df_region.columns = [str(c).strip().replace('\n','') for c in df_region.columns]
            # 일자, 계(total), 국내, 해외
            rename_map = {'일자': 'date', '계(명)': 'total', '국내발생(명)': 'domestic', '해외유입(명)': 'overseas'}
            df_region = df_region.rename(columns=rename_map)
            
            # 지역 컬럼만 선택
            target_regions = ['서울', '부산', '대구', '인천', '광주', '대전', '울산', '세종', 
                              '경기', '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주']
            valid_regions = [r for r in target_regions if r in df_region.columns]
            
            cols = ['date', 'total', 'domestic', 'overseas'] + valid_regions
            cols = [c for c in cols if c in df_region.columns]
            df_region = df_region[cols]
            df_region['date'] = pd.to_datetime(df_region['date'], errors='coerce')
            df_region = df_region.dropna(subset=['date'])
        
        # 1-3. 합치기 (확진/지역 + 사망)
        df_infection = pd.merge(df_region, df_death, on='date', how='left')
        
        # 숫자 정제
        for c in df_infection.columns:
            if c != 'date':
                df_infection[c] = df_infection[c].astype(str).str.replace(',', '').str.replace(' ', '')
                df_infection[c] = pd.to_numeric(df_infection[c], errors='coerce').fillna(0).astype(int)

        print(f"   ✅ 확진자 데이터 확보 완료 ({len(df_infection)}행)")

        # ---------------------------------------------------
        # [Step 2] 백신 데이터 처리 (C팀)
        # ---------------------------------------------------
        print("   -> 2단계: 백신 데이터 추출 및 합산 중...")
        path_vac = os.path.join(base_path, file_vac)
        if not os.path.exists(path_vac):
            print(f"❌ 오류: {file_vac} 파일이 없습니다.")
            return

        shutil.copyfile(path_vac, temp_vac)
        wb_vac = openpyxl.load_workbook(temp_vac, data_only=True)
        
        all_vac_data = pd.DataFrame()
        
        # 지역 시트만 골라서 데이터 수집
        regions = ['서울', '부산', '대구', '인천', '광주', '대전', '울산', '세종', 
                   '경기', '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주']
        valid_sheets = [s for s in wb_vac.sheetnames if s in regions]
        
        for sheet in valid_sheets:
            # 헤더 없이 읽어서 날짜(20210226.0) 찾기 (보통 5행)
            df_temp = pd.read_excel(temp_vac, sheet_name=sheet, header=4, engine='openpyxl')
            
            # 2번째 컬럼이 날짜라고 가정
            date_col = df_temp.columns[1]
            df_temp = df_temp.rename(columns={date_col: 'date'})
            
            # 날짜 변환 (숫자 -> 날짜)
            df_temp['date'] = df_temp['date'].astype(str).str.replace(r'\.0$', '', regex=True)
            df_temp['date'] = pd.to_datetime(df_temp['date'], format='%Y%m%d', errors='coerce')
            df_temp = df_temp.dropna(subset=['date'])
            
            # 나머지 숫자 데이터 합산 (일일 접종량)
            data_cols = df_temp.columns[2:]
            for c in data_cols:
                df_temp[c] = pd.to_numeric(df_temp[c].astype(str).str.replace(',',''), errors='coerce').fillna(0)
            
            df_temp['daily_vaccine_count'] = df_temp[data_cols].sum(axis=1)
            all_vac_data = pd.concat([all_vac_data, df_temp[['date', 'daily_vaccine_count']]])
            
        # 전국 합산
        df_vac_final = all_vac_data.groupby('date')['daily_vaccine_count'].sum().reset_index()
        df_vac_final['accumulated_vaccine_count'] = df_vac_final['daily_vaccine_count'].cumsum()
        
        print(f"   ✅ 백신 데이터 확보 완료 ({len(df_vac_final)}행)")

        # ---------------------------------------------------
        # [Step 3] 최종 통합 및 저장
        # ---------------------------------------------------
        print("   -> 3단계: 데이터 통합 및 저장...")
        
        # 확진자 데이터 기준으로 백신 데이터 결합 (Left Join)
        df_final = pd.merge(df_infection, df_vac_final, on='date', how='left')
        
        # 백신 빈칸(접종 시작 전) 0으로 채우기
        df_final['accumulated_vaccine_count'] = df_final['accumulated_vaccine_count'].fillna(0)
        df_final['daily_vaccine_count'] = df_final['daily_vaccine_count'].fillna(0)
        
        # 저장
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        df_final.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        # 임시 파일 삭제
        if os.path.exists(temp_inf): os.remove(temp_inf)
        if os.path.exists(temp_vac): os.remove(temp_vac)

        print("\n" + "="*50)
        print("🎉 [초기화 완료] 모든 데이터가 깨끗하게 재생성되었습니다!")
        print(f"📊 저장 경로: {output_file}")
        print("="*50)

    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    reset_and_build_data()