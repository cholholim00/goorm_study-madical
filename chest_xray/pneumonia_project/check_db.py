import sqlite3
from pathlib import Path

# ⚠️ 너 app.py에서 DB를 BASE_DIR / "db" / "predictions.db" 로 만들었으면 이거 그대로 쓰면 됨
db_path = Path("data/predictions.db")   # <-- 원래는 db/predictions.db 였을 거야
print("✅ DB 존재 여부:", db_path.exists(), db_path)

if not db_path.exists():
    raise SystemExit("DB 파일을 못 찾았어. 경로나 폴더 이름 다시 확인해야 해!")

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# 1) 테이블 목록 보기
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("📦 테이블 목록:", cur.fetchall())

# 2) 각 테이블에 몇 개 있는지 보기 (있으면 실행, 없으면 넘어감)
for table in ["xray_predictions", "clinical_predictions", "fusion_predictions", "prediction_logs"]:
    try:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]
        print(f"{table} 로그 개수:", count)
    except Exception as e:
        print(f"{table} 확인 중 에러(아마 테이블 없음): {e}")

# 3) prediction_logs / fusion_predictions 최근 5개만 보기
for table in ["prediction_logs", "fusion_predictions"]:
    try:
        print(f"\n=== {table} 최근 5개 ===")
        cur.execute(f"SELECT * FROM {table} ORDER BY id DESC LIMIT 5")
        rows = cur.fetchall()
        for r in rows:
            print(r)
    except Exception as e:
        print(f"{table} 조회 중 에러:", e)

conn.close()
