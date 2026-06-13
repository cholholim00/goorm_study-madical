# logs_stats.py
from pathlib import Path
from datetime import datetime
import sqlite3

import pandas as pd

# ===== 경로 설정 =====
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "predictions.db"
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

REPORT_PATH = REPORTS_DIR / "prediction_logs_summary.txt"


def main():
    # 1) DB 존재 여부 체크
    if not DB_PATH.exists():
        print(f"[ERROR] DB 파일을 찾을 수 없습니다: {DB_PATH}")
        print("FastAPI app에서 예측을 한 번이라도 돌려서 로그가 쌓였는지 확인하세요.")
        return

    print(f"[INFO] DB 경로: {DB_PATH}")

    # 2) 로그 읽기
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM prediction_logs ORDER BY id ASC", conn)
    conn.close()

    if df.empty:
        print("[INFO] prediction_logs 테이블이 비어 있습니다.")
        return

    # 3) 기본 통계
    total = len(df)
    by_endpoint = df["endpoint"].value_counts().to_dict()

    # endpoint별 개수
    n_xray = by_endpoint.get("xray", 0)
    n_clinical = by_endpoint.get("clinical", 0)
    n_fusion = by_endpoint.get("fusion", 0)

    # 4) 리스크 레벨 카운트 (fusion 기준)
    fusion_df = df[df["endpoint"] == "fusion"]
    fusion_risk_counts = fusion_df["risk_final"].value_counts(dropna=False).to_dict()

    # X-ray / clinical 리스크도 참고용으로 집계
    xray_df = df[df["endpoint"] == "xray"]
    xray_risk_counts = xray_df["risk_xray"].value_counts(dropna=False).to_dict()

    clin_df = df[df["endpoint"] == "clinical"]
    clin_risk_counts = clin_df["risk_clinical"].value_counts(dropna=False).to_dict()

    # 5) 확률 평균
    px_mean = df["p_xray"].mean(skipna=True)
    pc_mean = df["p_clinical"].mean(skipna=True)
    pf_mean = df["p_final"].mean(skipna=True)

    # 6) 리포트 텍스트 구성
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def risk_line(d: dict, label: str) -> str:
        return (
            f"- LOW: {d.get('LOW', 0)}\n"
            f"- MEDIUM: {d.get('MEDIUM', 0)}\n"
            f"- HIGH: {d.get('HIGH', 0)}\n"
        )

    report = []
    report.append("# Prediction Logs Summary")
    report.append(f"Generated at: {now}")
    report.append("")
    report.append("## 1. 전체 로그 개수")
    report.append(f"- total logs: {total}")
    report.append("")
    report.append("## 2. 엔드포인트별 로그 수")
    report.append(f"- xray: {n_xray}")
    report.append(f"- clinical: {n_clinical}")
    report.append(f"- fusion: {n_fusion}")
    report.append("")
    report.append("## 3. Risk Level 분포")
    report.append("### 3-1) Fusion (최종 위험도)")
    report.append(risk_line(fusion_risk_counts, "fusion").rstrip())
    report.append("")
    report.append("### 3-2) X-ray 모델 결과 (endpoint = xray)")
    report.append(risk_line(xray_risk_counts, "xray").rstrip())
    report.append("")
    report.append("### 3-3) 임상 모델 결과 (endpoint = clinical)")
    report.append(risk_line(clin_risk_counts, "clinical").rstrip())
    report.append("")
    report.append("## 4. 확률 평균값 (전체 로그 기준)")
    report.append(f"- mean p_xray:     {px_mean:.4f} (NaN이면 xray 로그가 없음)")
    report.append(f"- mean p_clinical: {pc_mean:.4f} (NaN이면 clinical 로그가 없음)")
    report.append(f"- mean p_final:    {pf_mean:.4f} (NaN이면 fusion 로그가 없음)")
    report.append("")
    report.append("※ 이 리포트는 D:/medical_project/data/predictions.db 의 prediction_logs 기준으로 생성됨.")

    report_text = "\n".join(report)

    # 7) 파일로 저장
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report_text)

    print(f"[INFO] 리포트 저장 완료: {REPORT_PATH}")
    print("------ Preview ------")
    print(report_text)


if __name__ == "__main__":
    main()
