# LivingCare 추론(Inference) 파이프라인

준상님의 Neo4j 지식그래프 위에 얹는 **추론 계층(RAG 검색 → 규칙 판단 → 로봇 intent 생성)** 코드.
자연어 "할머니 괜찮은지 확인해줘" 한 문장이 로봇 실행 intent가 되기까지의 전 과정을 담았다.

---

## 전체 흐름

```
자연어
  → [라우팅]  임베딩 유사도로 어느 축(axis)인지 판단        (준상님 코드 재사용)
  → [C1]      Neo4j 그래프에서 기기·기능·상태·규칙 조회      graph_retrieval.py
  → [관측값]  각 슬롯의 현재 값 준비 (State 비면 mock)       pipeline.py
  → [C2]      규칙 평가 = 판단 (코드가 결정, LLM 아님)        rule_evaluator.py
  → [게이트]  위험 기기는 저비용 센서 먼저 거쳤는지 확인      pipeline.py
  → [C3]      판단 결과를 로봇 intent로 조립 (LLM)            sequence_generator.py
```

**핵심 원칙:** 판단(위험한가)은 **코드가 규칙으로** 결정하고, LLM은 그 결정을 문장으로 **조립만** 한다.
그래프는 **읽기 전용(MATCH만, CREATE/SET 없음)** 으로만 접근한다.

---

## 파일 설명

| 파일 | 역할 |
|---|---|
| `graph_retrieval.py` | **C1** — Neo4j에서 축에 딸린 기기·기능·상태·규칙을 조회 (읽기 전용 Cypher) |
| `rule_evaluator.py` | **C2** — 관측값을 규칙 임계값과 비교해 `should_escalate` 판단 (결정론적, 데이터 주도) |
| `sequence_generator.py` | **C3** — 판단 결과를 로봇 intent로 생성. 백엔드: Ollama(무료) → Claude(유료) → mock |
| `pipeline.py` | 라우팅 + C1 + C2 + 게이트 + C3 통합. 5개 시나리오 데모 포함 |
| `trace_demo.py` | 한 시나리오가 단계마다 어떤 데이터로 변하는지 펼쳐 보는 학습용 |
| `call_trace_demo.py` | 어떤 함수가 어떤 순서로 호출되는지 추적 |

---

## 실행 준비물

1. **Neo4j** (준상님 그래프가 올라간 상태)
   - 예: Docker `neo4j:5.26`, 접속 `bolt://localhost:7687`, 계정 `neo4j`/`livingcare123`
   - `livingcare_graph_v2.cypher`를 Neo4j Browser에 붙여넣어 그래프 구축
2. **Python 패키지**
   ```bash
   pip install neo4j            # 그래프 조회
   # (선택) pip install sentence-transformers  # 진짜 임베딩 라우팅. 없으면 폴백(단어겹침)
   # (선택) pip install anthropic               # Claude 백엔드 쓸 때만
   ```
3. **Ollama** (C3 무료 로컬 LLM) — 선택
   - `ollama pull qwen2.5:7b` (기본 모델)
   - Ollama가 안 떠 있으면 C3는 자동으로 mock으로 폴백

> ⚠️ **의존성 주의:** 이 코드는 준상님 파일들과 **같은 폴더**에 있어야 실행된다.
> 필요한 준상님 파일: `end_to_end_pipeline.py`, `onto_axes.py`,
> `wellbeing_knowledge.py`·`safety_knowledge.py`·`comfort_knowledge.py`,
> `multi_axis_coordination.py`, `axis_worker.py`, `device_calling_pipeline.py`,
> `livingcare_registry.json`, `axis_centroids.json` 등.

---

## 실행 방법

```bash
# 전체 5개 시나리오 요약 실행
python pipeline.py

# 한 시나리오 단계별 데이터 추적 (질문/시각 바꿔가며 실험)
python trace_demo.py "할머니 괜찮은지 확인해줘" 15
python trace_demo.py "할머니 괜찮은지 확인해줘" 3      # 밤이라 판단이 달라짐
python trace_demo.py "방 온도 너무 낮은 거 아니야?" 15

# 함수 호출 순서 추적 (3개 예시)
python call_trace_demo.py
```

### 환경변수로 백엔드/접속 바꾸기
```bash
# C3 백엔드 강제 지정
LLM_BACKEND=mock       # 또는 ollama / claude
OLLAMA_MODEL=qwen2.5:7b
ANTHROPIC_API_KEY=...  # 있으면 Claude 사용 가능

# Neo4j 접속
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=livingcare123
```

---

## 지금 "진짜"인 것 vs "mock/스텁"인 것

| 구성요소 | 현재 | 나중에 교체 |
|---|---|---|
| Neo4j 그래프 조회 | ✅ 진짜 (준상님 데이터) | — |
| 규칙 판단(C2) / 안전 게이트 | ✅ 진짜 코드 | — |
| 센서 관측값 | ⚠️ mock (State 비어서) | 그래프 State 읽기 |
| C3 생성 | ✅ Ollama 무료 로컬 | 필요 시 Claude |
| 라우팅 임베딩 | ⚠️ 폴백(단어겹침) | sentence-transformers 설치 시 진짜 |
| 로봇 실제 실행 | ❌ 없음 (intent까지만) | agentic loop (담당 미정) |

> **계약(그래프 스키마)이 고정돼 있어서, mock을 실제로 갈아끼워도 코드는 안 바뀐다.**

---

## 팀과 결정할 것 (요약)

- **State**: 누가 쓰나 / 원본값 vs 가공값 / key 규약 / 읽기 권한 / 센서별 유무·신선도
- **에스컬레이션**: `requires_escalation_from`을 그래프에 넣을지 / phase 전환 기준 / 배터리 등 물리조건
- **함수명 한국어 매핑**: `ObserveFunction` → "관찰" (C3 출력 품질, 결정 없이 바로 가능)
- 한국어→영어 전환 여부(팀), DeviceKnowledge 채우기(근거 필요), 축·기기 확장

---

## 설계 원칙 (handoff.md 준수)

1. **판단은 코드, 생성은 LLM** — 위험도·임계값은 그래프 규칙, LLM은 조립만
2. **그래프는 읽기 전용** — State 말고는 수정 금지
3. **데이터 주도** — 축·기기·슬롯 이름 하드코딩 안 함. 준상님이 데이터 추가해도 코드 안 바뀜
4. **격리** — 모든 Cypher는 `graph_retrieval.py`에만. 스키마 바뀌면 여기만 수정
