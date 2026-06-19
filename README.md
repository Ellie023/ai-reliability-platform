# AI Reliability Platform

[![Repo](https://img.shields.io/badge/GitHub-ai--reliability--platform-181717?logo=github)](https://github.com/Ellie023/ai-reliability-platform)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-dashboard-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Tests](https://img.shields.io/badge/tests-18%20passing-brightgreen?logo=pytest&logoColor=white)](sample_repo/tests/test_order_service.py)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> Repository: **https://github.com/Ellie023/ai-reliability-platform**

---

## 문제 정의 — AI 에이전트 코드의 신뢰성

LLM 기반 AI 에이전트는 코드 패치를 자율적으로 생성합니다. 그러나 **에이전트가 생성한 코드가 실제로 안전한지 보장하는 메커니즘**은 대부분의 시스템에서 부재합니다.

- 에이전트가 의도치 않은 **회귀(regression)** 를 일으켜도 탐지되지 않는다.
- 실패의 **근본 원인(root cause)** 을 파악하기 어렵다.
- 어떤 패치가 위험한지 **우선순위**를 정할 기준이 없다.

이 플랫폼은 AI 에이전트가 제안한 패치를 **자동으로 평가하고, 회귀를 탐지하며, 위험도를 수치화**하는 평가 루프를 제공합니다. 자율 코딩 에이전트가 변경 사항을 머지하기 전에 반드시 통과해야 하는 **안전망(safety gate)** 역할을 합니다.

---

## 핵심 기능

| 기능 | 설명 |
|------|------|
| **패치 격리 적용** | `sample_repo`의 깨끗한 사본을 만들고 각 패치를 독립적으로 적용 |
| **자동 테스트 실행** | pytest를 실행하고 JSON 리포트로 결과를 수집 |
| **회귀 탐지** | 베이스라인 대비 새롭게 실패한 테스트를 정밀하게 식별 |
| **실패 분류** | 회귀를 검증 오류·상태 머신 오류·로직 오류 등 카테고리로 분류 |
| **근본 원인 가설 생성** | 실패 패턴으로부터 원인·영향도·수정 방향을 자동 추론 |
| **위험도 점수(Risk Score)** | 회귀·실패 수·타임아웃·변경 파일 수를 종합한 숫자 점수 산출 |
| **Streamlit 대시보드** | 패치별 결과, 고위험 패치, 상세 분석을 인터랙티브하게 시각화 |

---

## 아키텍처

```mermaid
flowchart TD
    subgraph INPUT["입력"]
        P["patches/*.patch\n(에이전트 생성 패치)"]
        SR["sample_repo/\n(FastAPI Order API)"]
    end

    subgraph EVAL["evaluator/ — 평가 파이프라인"]
        direction TB
        A["apply_patch.py\n격리된 작업 디렉토리 생성\n패치 적용 (patch -p1)"]
        B["run_tests.py\npytest 실행\nJSON 결과 수집"]
        C["detect_regression.py\n베이스라인 vs 패치 비교\n신규 실패 테스트 추출"]
        D["classify_failure.py\n실패 카테고리 분류\n(validation / state-machine / logic 등)"]
        E["generate_hypothesis.py\n근본 원인 추론\n영향도·수정 방향 생성"]
        F["risk_score.py\ncompute_risk_score()\n위험도 점수 산출"]
        A --> B --> C --> D --> E
        C --> F
    end

    subgraph OUTPUT["출력"]
        R1["results/<case>.json\n케이스별 상세 결과"]
        R2["results/summary.json\n전체 집계"]
        R3["reports/report.md\n마크다운 리포트"]
    end

    subgraph DASH["dashboard/"]
        G["streamlit_app.py\n인터랙티브 대시보드\nHigh Risk Patches 섹션 포함"]
    end

    P --> A
    SR --> A
    E --> R1
    F --> R1
    R1 --> R2
    R2 --> R3
    R2 --> G
```

### 위험도 점수 계산

```
risk_score = 0
  + 50   if regression detected
  + 10   × failed_tests count
  + 20   if test run timed out
  + 10   if changed_files >= 3

risk_level = HIGH   if score >= 50
           = MEDIUM if score >= 20
           = LOW    otherwise
```

---

## 프로젝트 구조

```
ai-reliability-platform/
├── sample_repo/                    # 평가 대상 시스템 (FastAPI Order API)
│   ├── app/
│   │   ├── models.py               # Pydantic 모델 + OrderStatus enum
│   │   ├── order_service.py        # 비즈니스 로직 (검증, 할인, 상태 머신)
│   │   └── main.py                 # FastAPI 엔드포인트
│   └── tests/
│       └── test_order_service.py   # pytest 18개 테스트
├── patches/                        # 에이전트 생성 패치
│   ├── agent_case_01.patch         # BUG: 빈 주문 허용
│   ├── agent_case_02.patch         # BUG: 100% 초과 할인 허용
│   ├── agent_case_03.patch         # BUG: 음수 가격 허용
│   ├── agent_case_04.patch         # BUG: 잘못된 상태 전환 허용
│   ├── agent_case_05.patch         # OK : count_items() 헬퍼 추가
│   └── agent_case_06.patch         # OK : can_cancel() 헬퍼 추가
├── evaluator/
│   ├── apply_patch.py              # 작업 사본 생성 + 패치 적용
│   ├── run_tests.py                # pytest 실행 + JSON 결과 파싱
│   ├── detect_regression.py        # 베이스라인 vs 패치 비교
│   ├── classify_failure.py         # 실패 분류 (카테고리/레이블)
│   ├── generate_hypothesis.py      # 근본 원인 + 수정 방향 추론
│   ├── risk_score.py               # compute_risk_score() 구현
│   └── generate_report.py          # 파이프라인 오케스트레이터
├── dashboard/
│   └── streamlit_app.py            # 인터랙티브 대시보드
├── reports/                        # 생성된 마크다운 리포트
├── results/                        # 생성된 JSON 결과
├── requirements.txt
└── README.md
```

---

## 실행 방법

### 1. 환경 설정

```bash
cd ~/ai-reliability-platform
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 평가 파이프라인 실행

```bash
python evaluator/generate_report.py
```

출력 파일:

- `results/<case>.json` — 패치별 상세 결과 (회귀, 분류, 가설, 위험도)
- `results/summary.json` — 전체 집계 (케이스 수, 회귀 수, 고위험 수)
- `reports/report.md` — 사람이 읽을 수 있는 마크다운 리포트

예상 결과: 케이스 01–04 → **REGRESSION** (분류된 원인 포함), 케이스 05–06 → **SAFE**

### 3. 대시보드 실행

```bash
streamlit run dashboard/streamlit_app.py
```

브라우저에서 `http://localhost:8501` 접속. High Risk Patches 섹션에서 위험도 높은 패치를 즉시 확인할 수 있습니다.

### 4. 샘플 API 직접 실행 (선택)

```bash
cd sample_repo
uvicorn app.main:app --reload
# http://127.0.0.1:8000/docs
```

---

## 패치 판정 흐름

1. **Isolate** — `sample_repo/`를 `results/_work/<case>/`에 복사
2. **Apply** — `patch -p1`로 후보 패치 적용
3. **Test** — pytest 실행 (JSON 리포트)
4. **Detect** — 베이스라인 대비 신규 실패 테스트 추출
5. **Classify** — 실패를 카테고리로 매핑
6. **Hypothesize** — 원인·영향도·심각도·수정 방향 출력
7. **Score** — 위험도 점수 산출 및 HIGH/MEDIUM/LOW 분류

**SAFE** 판정은 신규 실패 테스트가 **0개**일 때만 부여됩니다.

---

## 확장 방향

### Kubernetes Job 기반 병렬 평가

현재는 단일 프로세스에서 순차적으로 패치를 평가합니다. 수백 개의 패치를 처리하려면 각 패치 평가를 **k8s Job**으로 제출하고 결과를 오브젝트 스토리지(S3/GCS)에서 수집하는 구조로 확장할 수 있습니다.

```
Patch Queue → Job Dispatcher → k8s Job (per patch) → Results Aggregator
```

### 실제 GitHub PR 연동

`patches/` 디렉토리의 로컬 `.patch` 파일 대신, **GitHub Pull Request의 diff**를 직접 수신하는 워크플로우로 확장할 수 있습니다.

- GitHub Actions webhook → 평가 파이프라인 트리거
- PR 코멘트에 위험도 점수 및 실패 분류 자동 게시
- HIGH risk PR은 자동으로 merge 차단

### LLM 기반 가설 고도화

현재 `generate_hypothesis.py`는 규칙 기반 추론을 사용합니다. Claude API를 연동해 실제 코드 변경 내용과 실패 로그를 LLM에 전달하면 더 정교한 근본 원인 분석과 수정 제안을 생성할 수 있습니다.

```python
# 예시: Claude로 가설 생성
response = anthropic.messages.create(
    model="claude-opus-4-8",
    messages=[{"role": "user", "content": f"Patch diff:\n{diff}\n\nFailing tests:\n{failures}\n\nRoot cause?"}]
)
```

---

## License

Released under the [MIT License](LICENSE).
