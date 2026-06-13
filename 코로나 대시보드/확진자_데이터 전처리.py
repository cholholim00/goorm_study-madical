import pandas as pd
import os
import shutil

# 1. 파일 경로 설정
base_path = os.path.dirname(os.path.abspath(__file__))
original_file = '질병관리청_코로나19 확진자 발생현황(전수감시)_20230831.csv'
original_path = os.path.join(base_path, original_file)
temp_excel_file = 'temp_covid_final.xlsx'
temp_excel_path = os.path.join(base_path, temp_excel_file)

def final_merge_data_v2():
    try:
        print("🚀 [최종 V2] 사망자 및 지역 데이터 통합 복구를 시작합니다...")
        
        # 엑셀로 변환
        shutil.copyfile(original_path, temp_excel_path)
        xl = pd.ExcelFile(temp_excel_path, engine='openpyxl')
        sheets = xl.sheet_names
        
        # -------------------------------------------------------
        # 1단계: 첫 번째 시트에서 '사망자' 찾기 (강력한 검색 기능 탑재)
        # -------------------------------------------------------
        df_main = xl.parse(sheets[0], skiprows=4)
        df_main.columns = [str(c).strip() for c in df_main.columns]
        
        # [핵심] '사망'이라는 글자가 들어간 컬럼을 자동으로 찾습니다.
        death_col_name = None
        for col in df_main.columns:
            if '사망' in col:
                death_col_name = col
                break
        
        # 컬럼 이름 변경 매핑
        rename_map = {
            '일자': 'date', '계(명)': 'total', 
            '국내발생(명)': 'domestic', '해외유입(명)': 'overseas'
        }
        if death_col_name:
            rename_map[death_col_name] = 'death' # 찾은 컬럼을 death로 지정
            print(f"✅ 사망자 컬럼을 찾았습니다: '{death_col_name}'")
        else:
            print("⚠️ 경고: 사망자 컬럼을 찾지 못했습니다. (0으로 처리됨)")

        df_main = df_main.rename(columns=rename_map)
        
        # 필요한 컬럼만 정리
        if 'death' not in df_main.columns:
            df_main['death'] = 0
            
        main_cols = ['date', 'total', 'domestic', 'overseas', 'death']
        df_main = df_main[[c for c in main_cols if c in df_main.columns]]
        
        # 날짜 변환
        df_main = df_main[df_main['date'].astype(str).str.contains('20', na=False)]
        df_main['date'] = pd.to_datetime(df_main['date'])

        # -------------------------------------------------------
        # 2단계: 지역 데이터 시트 찾기
        # -------------------------------------------------------
        df_region = pd.DataFrame()
        for sheet in sheets:
            temp = xl.parse(sheet, header=None)
            # '서울'이 포함된 행 찾기
            header_idx = -1
            for idx, row in temp.iterrows():
                if any('서울' in str(x) for x in row.values):
                    header_idx = idx
                    break
            if header_idx != -1:
                df_region = xl.parse(sheet, header=header_idx)
                break
        
        # 지역 데이터 정리
        if not df_region.empty:
            df_region.columns = [str(c).strip() for c in df_region.columns]
            if '일자' in df_region.columns:
                df_region = df_region.rename(columns={'일자': 'date'})
            
            target_regions = ['서울', '부산', '대구', '인천', '광주', '대전', '울산', '세종', 
                              '경기', '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주']
            found_regions = [r for r in target_regions if r in df_region.columns]
            
            if 'date' in df_region.columns:
                df_region = df_region[['date'] + found_regions]
                df_region = df_region[df_region['date'].astype(str).str.contains('20', na=False)]
                df_region['date'] = pd.to_datetime(df_region['date'])

        # -------------------------------------------------------
        # 3단계: 병합 및 저장
        # -------------------------------------------------------
        if not df_region.empty:
            df_final = pd.merge(df_main, df_region, on='date', how='outer')
        else:
            df_final = df_main

        # 숫자 변환 및 0 채우기
        df_final = df_final.sort_values('date').reset_index(drop=True)
        for col in df_final.columns:
            if col != 'date':
                df_final[col] = df_final[col].astype(str).str.replace(',', '').str.replace(' ', '')
                df_final[col] = pd.to_numeric(df_final[col], errors='coerce').fillna(0).astype(int)

        # 저장
        output_path = os.path.join(base_path, 'data', 'cleaned_covid_data.csv')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df_final.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        if os.path.exists(temp_excel_path):
            os.remove(temp_excel_path)

        print("\n" + "="*50)
        print("🎉 [대성공] 사망자(A팀)와 지역(B팀) 데이터가 모두 들어있는 파일 완성!")
        print(f"📊 확인: 서울 {df_final.iloc[-1]['서울']}명 / 사망 {df_final.iloc[-1]['death']}명")
        print("="*50)

    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    final_merge_data_v2()