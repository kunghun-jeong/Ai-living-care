# 연구 자료 핸드오프 — MCP 기반 LIMO 로봇 제어 시스템

`MCP 대본.docx`, `MCP_LIMO_발표자료_완성본.pptx`(21슬라이드), 그리고 그 안에서 실제로 인용/참고한 논문 원문을 대조 확인해서 정리한 문서. 다른 AI가 이 프로젝트의 연구 배경을 처음부터 다시 뒤지지 않도록 하는 게 목적. 확신도가 다른 두 그룹으로 나눔: **① PPT/대본에 직접 인용되거나 내용이 정확히 일치해서 확인된 것**, **② 프로젝트와 관련은 있지만 이 PPT에 직접 쓰였다는 확증은 없는 것**.

## 0. 이 프로젝트의 위치

지도교수(정재훈, 성균관대 소프트웨어학과)의 상위 연구과제: **"AI 에이전트 기반 능동형 생활지원을 위한 지능형 리빙케어 프레임워크"** (`AI-Agent-LivingCare-Framework-Project-20260515-v1.pdf/pptx`). MCP_LIMO 데모 시나리오("할머니의 상태를 확인해줘")가 바로 이 리빙케어 프레임워크의 구체적인 축소 구현 사례임. LIMO+MCP 작업은 이 상위 과제의 서브 트랙.

## 1. 발표 흐름 (MCP 대본.docx + MCP_LIMO_발표자료_완성본.pptx, 21슬라이드)

1. **기존 연구의 문제점** (슬라이드 2-3) — 로보틱스 Perception-Judgment-Action을 world model 기반 end-to-end 강화학습으로 설계하려다 포기한 과정
2. **대안 — MCP** (슬라이드 4-8) — 교수님 제안으로 MCP 도입, client-server/JSON-RPC 구조 설명
3. **우리 시스템 구조: Manager-Worker** (슬라이드 9-13) — RCP 논문에서 아이디어를 얻어 자체 아키텍처 설계, Perception/Reasoning/Action 함수 분리
4. **실제 활용 — 코드/실행결과** (슬라이드 14-17) — MCP 서버 코드, "할머니 상태 확인" 시나리오, mock 서버로 배선 검증
5. **부록** (슬라이드 18-20) — JSON-RPC 2.0, stdio vs HTTP, MCP 서버 구성
6. **결론** (슬라이드 21) — MCP 배선 검증 완료, 다음 단계는 worker function 구체화 + 시나리오 작성 → **오늘(8/3~4) 세션에서 한 patrol/dock/interrupt 작업이 바로 이 다음 단계임** (`SESSION_HANDOFF.md` 참고)

## 2. PPT/대본에 직접 인용·확인된 자료 (확신도 높음)

### 2.1 Robot Context Protocol (RCP)
`AIPapers/Robot Context Protocol (RCP) A Runtime-Agnostic.pdf` — 슬라이드 9에 논문 제목·저자가 그대로 인용됨 ("우리 시스템의 구조: Manager-Worker" 섹션에서).

- Lee & Lau, arXiv:2506.11650 (2025), IEEE RA-L
- **핵심**: 로봇 시스템 내부 복잡도를 추상화하는 경량 미들웨어-비의존적 통신 프로토콜. HTTP/WebSocket 위에서 schema 기반 메시지(read/write/execute/subscribe)로 client-facing 연산과 backend 구현을 분리. 물리 로봇/클라우드 오케스트레이터/시뮬레이션 등 다양한 배포 환경을 하나의 인터페이스로 통일하는 게 목표.
- **우리 프로젝트와의 연결**: RCP는 "로봇 제어를 표준화된 스키마로 추상화한다"는 아이디어를 줌. 우리는 이를 MCP(JSON-RPC 2.0 + stdio)로 직접 구현 — RCP가 HTTP/WebSocket을 쓰는 반면 우리는 로컬 엣지 환경이라 stdio를 채택한 게 차이점 (대본: "저희 엣지는 로컬서버를 활용하기에 stdio를 채택했습니다").

### 2.2 World model 기반 end-to-end 강화학습 (기각된 접근) — Danijar Hafner 계열 3편
슬라이드 2 인용문: *"논문에서는 world model latent 공간 위의 단일 연속/이산 목표 하나를 제안하도록 설계되어 있는데... 하나의 강화학습 정책이 이들을 동시에 다루도록 학습시키는 것은... 현실적이지 않다."* / 대본: *"world모델은 RSSM을 활용한 비지도 학습을 해서 미래 상황을 예측"*

세 편 다 Danijar Hafner(당시 Google Brain/DeepMind)가 저자로, RSSM(Recurrent State-Space Model) 계열 world model 논문들:

- **`Learning Latent Dynamics for Planning from Pixels.pdf`** (PlaNet, ICML 2019) — RSSM(결정론적+확률적 전이를 결합한 latent dynamics model) 원조 논문. "latent overshooting"으로 멀티스텝 예측 정확도 향상.
- **`DREAM TO CONTROL LEARNING BEHAVIORS.pdf`** (Dreamer, ICLR 2020) — world model의 latent space 안에서 상상된 궤적으로 behavior를 학습(latent imagination). "단일 목표"에 최적화된 policy를 latent space 위에서 학습한다는 게 슬라이드 2의 비판 대상과 정확히 일치.
- **`MASTERING ATARI WITH DISCRETE WORLD MODELS.pdf`** (DreamerV2, ICLR 2021) — discrete latent representation으로 개선된 버전, Atari 55종에서 인간 수준 달성.

**우리 팀의 결론(기각 사유)**: 이 논문들은 "도달 가능한 미래 상태"라는 단일 metric으로 목표를 환원하는 구조인데, 우리 시스템이 필요로 하는 서브골("카메라 활성화", "사물 인식 수행" 등)은 성격이 서로 다른 다수의 이산 명령이라 단일 강화학습 정책으로 다루기엔 샘플 복잡도·보상 설계 양쪽에서 비현실적이라고 판단 → RL 포기, MCP로 전환하는 계기가 됨.

### 2.3 Disentangled representation의 이론적 한계
슬라이드 3 인용문과 **거의 토씨 하나 안 틀리고 일치**: *"아무리 encoding을 orthonormal하게 하더라도 decoding 결과가 disentangled인지 entangled인지 데이터만으로는 절대 알 수 없다는 것을 증명"*

- **`Challenging Common Assumptions in the Unsupervised Learning of.pdf`** (Locatello et al., ICML 2019, 정확한 제목: *Challenging Common Assumptions in the Unsupervised Learning of Disentangled Representations*)
- **핵심 결과**: "비지도 학습으로 disentangled representation을 학습하는 것은 모델과 데이터 양쪽에 inductive bias 없이는 이론적으로 불가능하다"를 증명 (impossibility theorem). 12,000개 이상 모델을 7개 데이터셋에서 학습시켜 실증적으로도 확인 — disentanglement 정도가 downstream task의 sample complexity를 줄여주지도 않았음.
- **우리 프로젝트와의 연결**: world model(RSSM)의 latent state가 "목표별로 깔끔하게 분리된" 표현을 만들어줄 거라 기대할 수 없다는 근거로 인용 — 위 2.2의 RL 접근을 최종적으로 기각하는 이론적 근거.

### 2.4 MCP 프로토콜 자체 설명 자료
슬라이드 5-7에 3번 반복 인용된 GitHub 링크: `https://github.com/asinghcsu/model-context-protocol-survey#comparative-analysis-mcp-vs-traditional-apis` — 논문이 아니라 MCP vs 전통적 API 비교 다이어그램 출처. Client-server, transport layer, orchestrator 개념도를 여기서 가져옴.

## 3. 프로젝트와 관련은 있지만 이 PPT에 직접 쓰였다는 확증은 없는 것

### 3.1 Manager-Worker 명명 관련 — FeUdal Networks
- **`FeUdal Networks for Hierarchical Reinforcement Learning.pdf`** (Vezhnevets et al., DeepMind, ICML 2017) — 초록에 *"Our framework employs a Manager module and a Worker module. The Manager operates at a lower temporal resolution and sets abstract goals... The Worker generates primitive actions"* 라고 명시. 우리 아키텍처의 "Manager(=MCP client, Claude API)/Worker(=MCP server, LIMO)" 용어와 개념적으로 거의 동일한 분리 구조.
- PPT에 직접 인용되진 않았지만, RL 계열 논문을 조사하던 흐름(2.2) 안에서 자연스럽게 봤을 가능성이 높음 — 확실친 않으니 "직접 인용"이 아니라 "개념적 연결고리 후보"로만 남김.
- 같은 흐름의 관련 논문: `Deep Hierarchical Planning from Pixels.pdf` (Director, Hafner et al. — latent space 안에서 상위 정책이 하위 목표를 정하고 하위 정책이 실행하는 계층 구조, Manager-Worker와 유사한 문제의식).

### 3.2 Intent 기반 네트워크 관리 — Robotron
- **`Robotron Top-down Network Management at Facebook.pdf`** (SIGCOMM 2016) — 엔지니어가 상위 수준 design intent를 표현하면 이를 저수준 장비 설정으로 자동 번역·배포하는 시스템. "intent → 저수준 실행"으로 번역한다는 패턴이 이 프로젝트 팀의 다른 트랙(I2NSF/intent-translator, `Intent_Management_system` 프로젝트)과 직접 맞닿아 있음. MCP_LIMO 슬라이드에 명시적으로 인용되진 않았지만, 팀이 이 concept(intent 분리)에 익숙한 배경이라 자연스럽게 참고했을 가능성이 있음.

### 3.3 최근 로보틱스 논문 (2026년 7-8월 다운로드, 이 세션과 겹치는 시기)
PPT엔 안 나오지만 `AIPapers` 폴더에 최근 날짜로 있어서 팀이 병행해서 읽고 있었을 것으로 보이는 것들 — 확인은 안 했지만 참고용으로 남김:
- `RoboTTT Context Scaling for Robot Policies.pdf` (NVIDIA, 2026-07) — 로봇 foundation model의 context 길이를 8K timestep까지 늘리는 test-time training 기법.
- `Diagnosing Compositional Generalization in Sequential Robot Tasks.pdf` (Berkeley, 2026-08) — 순차 로봇 조작 태스크에서 instruction 조합 일반화 진단.
- `Data Pyramid for Embodied Manipulation.pdf` (2026-07) — embodied 로봇 학습 데이터 소스를 5개 계층(피라미드)으로 정리한 서베이.

### 3.4 확인 결과 관련 없는 것 (오탐)
- **`Separating Intent from Execution A.pdf`** — 제목만 보면 "intent와 execution 분리"라 이 프로젝트와 관련 있어 보이지만, 실제로는 **야구 투수의 제구력(pitch control) 통계 분석 논문**(xCTRL 메트릭)임. "Intent"라는 단어가 겹치는 우연. 이 프로젝트와 무관 — 나중에 "Intent 관련 자료"로 착각해서 다시 열어보지 않도록 명시해둠.

## 4. Confucius / S12Framework — 별도 트랙 (참고만)

`Confucius_Framework_PPT.pptx`, `S12Framework/` 폴더는 이번 MCP_LIMO 발표와는 **다른 트랙**으로 보임 (SIGCOMM'25 Confucius 설계를 LIMO cloud-edge에 적용하는 방향 — 기존 메모리 `project_intent_framework.md` 참고). 이 문서에서는 안 파고들었음. 필요하면 `S12Framework/03_framework_concerns.md`부터 볼 것.

## 5. 파일 위치 요약

| 자료 | 경로 |
|---|---|
| 대본 | `산학협력/MCP 대본.docx` |
| 완성 PPT | `산학협력/MCP_LIMO_발표자료_완성본.pptx` (초안: `..._초안.pptx`) |
| RCP 논문 | `AIPapers/Robot Context Protocol (RCP) A Runtime-Agnostic.pdf` |
| World model 3편 | `AIPapers/Learning Latent Dynamics for Planning from Pixels.pdf`, `DREAM TO CONTROL LEARNING BEHAVIORS.pdf`, `MASTERING ATARI WITH DISCRETE WORLD MODELS.pdf` |
| Disentanglement 논문 | `AIPapers/Challenging Common Assumptions in the Unsupervised Learning of.pdf` |
| 리빙케어 상위과제 | `산학협력/AI-Agent-LivingCare-Framework-Project-20260515-v1.pdf` (+ `.pptx`) |
| 오늘 코드 작업 요약 | `limo_slam/SESSION_HANDOFF.md` |
