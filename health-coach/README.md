# 🩺 AI 혈압 코치 대시보드 (Health Coach Web & API)

개인 혈압·혈당 기록을 모아서 **대시보드, AI 코치, 라이프스타일 인사이트, 코칭 히스토리**까지 제공하는
풀스택 헬스케어 미니 프로젝트입니다.

- 프론트엔드: **Next.js 15 (App Router) + TypeScript + Tailwind CSS**
- 백엔드: **Express + Prisma + SQLite + JWT 인증**
- AI: **OpenAI Responses API (gpt-4.1-mini)**

> 목표:  
> “누가 봐도 실용적이고 잘 정리된 **AI 헬스케어 포트폴리오 프로젝트** 하나 만들기”

---

## 💡 주요 기능 (버전별)

### ✅ Version 1 — 기본 건강 기록 & 대시보드

- 혈압 / 혈당 기록 저장
  - 수축기(`value1`), 이완기(`value2`), 상태(`state`), 메모(`memo`)
- 최근 7일 요약 대시보드 (`/`)
  - 최근 측정값
  - 최근 7일 평균 혈압 / 평균 혈당
  - 최근 기록 리스트 (최대 10개)
- 혈압 범위 자동 분류
  - 정상 / 상승 / 1단계 / 2단계 의심
- 라인 차트 (`/charts`)
  - 최근 N일(7/14/30) 혈압 추이 시각화
- 샘플 데이터
  - 2주치 랜덤 혈압 데이터 자동 생성 (개발용)
  - 모든 기록 한 번에 삭제(초기화) 버튼

---

### ✅ Version 2 — 목표 혈압 & AI 혈압 코치

- 🎯 **목표 혈압 설정 (`/settings`)**
  - `UserProfile` 테이블로 목표 수축기/이완기 저장
  - 대시보드/AI 코치에서 목표 값과 비교

- 🤖 **AI 코치 페이지 (`/ai-coach`)**
  - 최근 N일(7/14/30) 요약 데이터 조회
  - 사용자가 직접 `현재 상태 / 고민` 메모 입력
  - OpenAI Responses API로:
    - 최근 평균 혈압, 최근 측정값, 상태 라벨, 메모, 목표 혈압을 한 번에 보내고
    - 부드러운 한국어 존댓말 코멘트 생성
  - “의사”가 아닌 “생활 습관 코치” 톤으로 답변 (진단/치료 지시 X)

---

### ✅ Version 2.5 — 라이프스타일 인사이트 & AI 코칭 히스토리

#### 1) 라이프스타일 인사이트 (`/insights`)

혈압 기록에 다음 필드를 추가해서, **생활 습관별 혈압 차이**를 통계로 확인합니다.

- `sleepHours`: 수면 시간
- `exercise`: 운동 여부 (`true` / `false`)
- `stressLevel`: 스트레스 지수 (1~5)

백엔드에서 그룹별 평균 혈압 계산:

- 수면
  - 6시간 미만 vs 6시간 이상
- 운동
  - 운동한 날 vs 운동 안 한 날
- 스트레스
  - 낮음(1~2), 중간(3), 높음(4~5)

프론트 `/insights`에서 테이블/배지 형태로 시각화하고,  
**“🧠 AI 인사이트 받기” 버튼**으로:

- 데이터 기반으로 “경향/가능성”만 조심스럽게 설명
- 마지막에는 항상 “참고용이며, 정확한 판단은 의료 전문가 상담” 안내

#### 2) AI 코치 히스토리 (`/ai-history`)

OpenAI 호출 결과를 **DB에 로그로 저장**해서 타임라인처럼 조회합니다.

Prisma 모델 예시:

```prisma
model AiCoachLog {
  id        Int      @id @default(autoincrement())
  userId    Int
  createdAt DateTime @default(now())
  type      String      // "coach" | "lifestyle" 등
  rangeDays Int
  userNote  String?
  source    String?
  aiMessage String

  user      User       @relation(fields: [userId], references: [id])
}
```
# 🩺 AI 혈압 코치 대시보드 (Health Coach Web & API)

개인 혈압·혈당 기록을 모아서 **대시보드, AI 코치, 라이프스타일 인사이트, 코칭 히스토리**까지 제공하는
풀스택 헬스케어 미니 프로젝트입니다.

- 프론트엔드: **Next.js 15 (App Router) + TypeScript + Tailwind CSS**
- 백엔드: **Express + Prisma + SQLite + JWT 인증**
- AI: **OpenAI Responses API (gpt-4.1-mini)**

> 목표:  
> “누가 봐도 실용적이고 잘 정리된 **AI 헬스케어 포트폴리오 프로젝트** 하나 만들기”

---

## 💡 주요 기능 (버전별)

### ✅ Version 1 — 기본 건강 기록 & 대시보드

- 혈압 / 혈당 기록 저장
  - 수축기(`value1`), 이완기(`value2`), 상태(`state`), 메모(`memo`)
- 최근 7일 요약 대시보드 (`/`)
  - 최근 측정값
  - 최근 7일 평균 혈압 / 평균 혈당
  - 최근 기록 리스트 (최대 10개)
- 혈압 범위 자동 분류
  - 정상 / 상승 / 1단계 / 2단계 의심
- 라인 차트 (`/charts`)
  - 최근 N일(7/14/30) 혈압 추이 시각화
- 샘플 데이터
  - 2주치 랜덤 혈압 데이터 자동 생성 (개발용)
  - 모든 기록 한 번에 삭제(초기화) 버튼

---

### ✅ Version 2 — 목표 혈압 & AI 혈압 코치

- 🎯 **목표 혈압 설정 (`/settings`)**
  - `UserProfile` 테이블로 목표 수축기/이완기 저장
  - 대시보드/AI 코치에서 목표 값과 비교

- 🤖 **AI 코치 페이지 (`/ai-coach`)**
  - 최근 N일(7/14/30) 요약 데이터 조회
  - 사용자가 직접 `현재 상태 / 고민` 메모 입력
  - OpenAI Responses API로:
    - 최근 평균 혈압, 최근 측정값, 상태 라벨, 메모, 목표 혈압을 한 번에 보내고
    - 부드러운 한국어 존댓말 코멘트 생성
  - “의사”가 아닌 “생활 습관 코치” 톤으로 답변 (진단/치료 지시 X)

---

### ✅ Version 2.5 — 라이프스타일 인사이트 & AI 코칭 히스토리

#### 1) 라이프스타일 인사이트 (`/insights`)

혈압 기록에 다음 필드를 추가해서, **생활 습관별 혈압 차이**를 통계로 확인합니다.

- `sleepHours`: 수면 시간
- `exercise`: 운동 여부 (`true` / `false`)
- `stressLevel`: 스트레스 지수 (1~5)

백엔드에서 그룹별 평균 혈압 계산:

- 수면
  - 6시간 미만 vs 6시간 이상
- 운동
  - 운동한 날 vs 운동 안 한 날
- 스트레스
  - 낮음(1~2), 중간(3), 높음(4~5)

프론트 `/insights`에서 테이블/배지 형태로 시각화하고,  
**“🧠 AI 인사이트 받기” 버튼**으로:

- 데이터 기반으로 “경향/가능성”만 조심스럽게 설명
- 마지막에는 항상 “참고용이며, 정확한 판단은 의료 전문가 상담” 안내

#### 2) AI 코치 히스토리 (`/ai-history`)

OpenAI 호출 결과를 **DB에 로그로 저장**해서 타임라인처럼 조회합니다.

Prisma 모델 예시:

```prisma
model AiCoachLog {
  id        Int      @id @default(autoincrement())
  userId    Int
  createdAt DateTime @default(now())
  type      String      // "coach" | "lifestyle" 등
  rangeDays Int
  userNote  String?
  source    String?
  aiMessage String

  user      User       @relation(fields: [userId], references: [id])
}
```