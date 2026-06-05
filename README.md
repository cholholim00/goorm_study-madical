# goorm_study-madical : 🏥 실시간 진료과 분류 및 의료 NER 통합 서빙 플랫폼

> **2026년도 졸업 프로젝트 (Medical AI Full-Stack Prototype)**
> 환자의 자각 증상 발화 및 임상 소견 스크립트를 입력받아, **[진료과 분류(Classification)]**와 **[의료 핵심 개체명 인식(NER)]** 태스크를 단일 파이프라인에서 동시 연산하고 실시간 메디컬 대시보드로 시각화하는 AI 풀스택 서빙 아키텍처 시스템입니다.

---

## 🏗️ 1. 전체 시스템 아키텍처 (System Architecture)

본 프로젝트는 대용량 의료 질의응답 코퍼스를 가공하여 두 개의 서로 다른 Roberta-Large 가중치 엔진을 구축하고, FastAPI 백엔드 레이어에서 GPU 메모리에 동시 적재(Warm-up)하여 서빙합니다.

[Client: React Dashboard] (Port: 5173)
│ (비동기 Axios POST 요청 / CORS 패치 완수)
▼
[Backend: FastAPI Server] (Port: 8000) ── (Startup 레이어 멀티 모델 GPU 가중치 사전 적재)
│
├─▶ [Task 1: KLUE-Roberta-Large 분류기] ──▶ 진료과별 소프트맥스 확률 가속 분포 계산
└─▶ [Task 2: KLUE-Roberta-Large NER]   ──▶ Word_IDs 인덱스 트래커 기반 글자 단위 질환명 추출


---

## 📊 2. Phase 1: 환자 증상 기반 진료과 분류 (Text Classification)

### 💡 데이터 불균형 극복 및 고도화 엔지니어링 소정
* **기반 베이스라인 모델:** `klue/roberta-large`
* **문제 정의:** 1차 학습 결과, 전체 Accuracy는 97.3%로 준수했으나 데이터 풀이 희소한 **여성질환 (F1: 0.9279)** 및 **응급질환 (F1: 0.9390)** 카테고리에서 치명적인 오진 구멍 발견.
* **적용 핵심 패치:**
  1. 원본 데이터셋 풀에서 약점 클래스 데이터 집중 타겟팅 업샘플링 (약 4배 증폭, 총 28,000개 데이터 세트 구축).
  2. 파이토치 `nn.CrossEntropyLoss(weight=class_weights_tensor)` 파이프라인을 커스텀 Trainer에 주입하여 불균형 레이블에 대한 오답 패널티 가중치 차등 부여.

### 📈 최종 파이널 성능 지표 (Confusion Matrix 기반 튜닝 결과)
* **전체 앙상블 Accuracy:** **`97.75%`** (+0.45% 성능 향상)
* **여성질환 F1-Score:** **`0.9554`** (+0.0275 개선 / Recall `0.9907` 달성으로 오진 확률 최소화)
* **응급질환 F1-Score:** **`0.9358`** (Recall `96.23%` 저지선 확보로 위급 환자 누락 방지 안정성 강화)

---

## 🏷️ 3. Phase 2: 의료 개체명 인식 (Named Entity Recognition)

### ✂️ 토큰 정렬(Token Alignment) 및 BIO 태깅 파이프라인
* **BIO 규칙 준수:** 문자열 단위(Char-level)로 정밀 분할 매핑 (`B-질환명`, `I-질환명`, `O`).
* **서브워드 토큰 동기화 이슈 해결:** BERT 계열 토크나이저의 형태소/서브워드 쪼개짐 현상으로 인한 차원 불일치 에러(`IndexError`)를 방지하기 위해 `tokenized_inputs.word_ids()` 트래커 파싱 함수 구축.
  * 특수 토큰(`[CLS]`, `[SEP]`, `[PAD]`) 및 분할 서브워드 예외 구역에 `-100` 패딩 처리를 수행하여 손실 값 계산 레이어 정밀 동기화 완료.
* **최종 수렴 스펙:** **Train Loss: `0.0413` / Eval Loss: `0.0310`** 수렴으로 문맥 내 정식 문헌 질환명 완벽 포착 수준 달성.

---

## 🛠️ 4. 기술 스택 (Tech Stacks)

### Backend & AI Infrastructure
* Python 3.10+, PyTorch (CUDA 가속 인프라)
* Miniconda Environment (Portable_GPU)
* Hugging Face Transformers (`RobertaForSequenceClassification`, `RobertaForTokenClassification`)
* FastAPI, Uvicorn, Pydantic, Scikit-learn, Pandas

### Frontend Dashboard
* React (Vite Fast Bundler Architecture)
* Axios, Lucide-React Component Icons

---

## 📂 5. 프로젝트 디렉토리 구조 (Directory Structure)

```text
goorm_study-madical/
├── Phase1/                             # 1단계: 진료과 분류 모델 아키텍처 부문
│   ├── best_advanced_model/            # 최적화 고도화 모델 가중치 바이너리 폴더
│   └── parsed_medical_sample.csv       # 가중치 라벨 인코더 매핑용 CSV
├── Phase2/                             # 2단계: 의료 NER 개체명 인식 아키텍처 부문
│   ├── 1단계_NER-BIO_태깅데이터셋_빌더.py # JSON 코퍼스 -> BIO 리스트 변환기
│   ├── 2단계_NER-토큰_정렬및학습.py       # word_ids 정렬 및 자율 학습 스크립트
│   └── best_ner_model/                 # 완벽 수렴된 NER 가중치 바이너리 폴더
├── Phase3/                             # 3단계: FastAPI 통합 서빙 아키텍처 부문
│   └── app.py                          # 멀티 가중치 GPU Warm-up 및 CORS 대응 API 코어
└── bridgeboard-ui/                     # 4단계: React 프론트엔드 대시보드 부문
    ├── src/
    │   └── App.jsx                     # 실시간 레포트 스크리닝 및 히스토리 관리 UI
    └── package.json
🚀 6. 설치 및 실행 가이드 (Quick Start)
Prerequisites (가상환경 진입)
Bash
# GPU 가속 환경 활성화
conda activate AI
1) Backend 가동 (FastAPI 통합 서빙)
Bash
cd Phase3
pip install fastapi uvicorn pydantic transformers torch pandas scikit-learn
uvicorn app:app --reload
서버가 정상 가동되면 🚀 [System] 모든 AI 엔진이 CUDA 가속 레이어에 정상 적재되었습니다! 로그가 출력되며 http://127.0.0.1:8000/docs에서 대화형 Swagger 문서 검증이 가능합니다.

2) Frontend 가동 (React Dashboard UI)
Bash
cd bridgeboard-ui
npm install
npm run dev