# 🦠 대한민국 코로나19 종합 분석 대시보드 (COVID-19 Dashboard)

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-5.18-3F4F75?style=flat&logo=plotly&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-Data%20Analysis-150458?style=flat&logo=pandas&logoColor=white)

## 📖 프로젝트 개요
이 프로젝트는 질병관리청 공공데이터를 활용하여 **코로나19 확진자, 사망자, 지역별 발생 현황 및 백신 접종 효과**를 분석하고 시각화한 **인터랙티브 웹 대시보드**입니다.

복잡한 원본 데이터(엑셀/CSV)를 정제 및 통합하여, 사용자가 직관적으로 데이터를 탐색할 수 있도록 구현하였습니다.

---

## 🚀 주요 기능 (Team Missions)

이 프로젝트는 3개의 분석 모듈(팀)로 구성되어 있습니다.

### 📈 Team A: 추이 분석 (Trend Analysis)
- **목표:** 팬데믹 기간 동안의 확진자 및 사망자 증감 추이 파악
- **기능:**
    - 일별 신규 확진자 및 사망자 수 시각화 (이중축 그래프)
    - 특정 기간(Date Range) 필터링 기능 제공

### 🗺️ Team B: 지역 분석 (Regional Analysis)
- **목표:** 전국 17개 시도별 확진자 발생 규모 비교
- **기능:**
    - 최신 날짜 기준 지역별 확진자 순위 바 차트(Bar Chart)
    - 사이드바를 통한 특정 지역 다중 선택 및 비교 기능

### 💉 Team C: 백신 분석 (Vaccine Efficacy)
- **목표:** 백신 접종률 증가가 사망자 감소에 미친 영향 분석
- **기능:**
    - 누적 백신 접종 수와 일일 사망자 수의 상관관계 시각화
    - 접종 확대 시기와 사망자 감소 시점의 패턴 분석

---

## 🛠️ 기술 스택 (Tech Stack)

| 구분 | 사용 기술 |
| :--- | :--- |
| **Language** | Python 3.11 |
| **Web Framework** | Streamlit (대시보드 UI/UX 구현) |
| **Visualization** | Plotly Express / Graph Objects (인터랙티브 차트) |
| **Data Processing** | Pandas, Openpyxl (데이터 전처리 및 통합) |
| **Data Source** | 질병관리청(KDCA) 공공 데이터 |

---

## 📂 프로젝트 구조 (Directory Structure)

```bash
팀미션: 코로나19 대시보드/
├── data/
│   └── cleaned_covid_data.csv    # 전처리가 완료된 통합 데이터
├── 질병관리청_코로나19 예방접종 통계 현황_20240805.csv
├── 질병관리청_코로나19 확진자 발생현황(전수감시)_20230831.csv
├── 확진자_데이터 전처리.py
├── 백신_데이터 전처리.py
├── A팀_추이 분석팀.py
├── B팀_발생 원인 분석팀.py
├── C팀_백신 접종률 vs 중증화율 상관관계 분석팀.py
├── app.py                       # 대시보드 실행 메인 파일 (Streamlit)
├── project_reset.py              # 데이터 전처리 및 초기화 스크립트
├── requirements.txt              # 필요 라이브러리 목록
└── README.md                     # 프로젝트 설명서