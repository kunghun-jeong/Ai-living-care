# 2026-08-18 · `graph_inference/`를 폐기하고 MAC 하위로 분배한다

> **정본 반영** `manager_ai_agent/CLAUDE.md` · `manager_ai_agent/manager_ai_core/CLAUDE.md` ·
> `manager_ai_agent/manager_ai_core/kg_mapping/CLAUDE.md` ·
> `manager_ai_agent/manager_ai_core/policy_generation/CLAUDE.md`

`manager_ai_agent/graph_inference/`(Neo4j 기반 라우팅→조회→판단→intent 생성 실험 파이프라인)는
`SOT.md` §2 구조에 없는 임시 폴더였다. `SOT.md`가 이미 정한 MAC 하위 구조
(`kg_mapping/`·`policy_generation/`)에 역할별로 옮겨, 새 컴포넌트를 만들지 않고도 정본 트리와
정합하게 했다.

## 옮긴 대응

| 옛 경로 | 새 경로 | 근거 |
|---|---|---|
| `graph_inference/graph_retrieval.py` (C1) | `manager_ai_core/kg_mapping/graph_retrieval.py` | 그래프 조회는 KG Mapping의 역할과 같은 층위(어구/축을 KG 값으로 해소) |
| `graph_inference/rule_evaluator.py` (C2) | `manager_ai_core/policy_generation/rule_evaluator.py` | 판단 결과(`should_escalate`)가 정본 L2의 `<condition>`·`<assurance>`에 대응될 후보 |
| `graph_inference/sequence_generator.py` (C3) | `manager_ai_core/policy_generation/sequence_generator.py` | LLM으로 L1(판단)을 L2(intent)로 조립 — policy_generation의 정의와 같은 동작 |
| `graph_inference/pipeline.py` · `trace_demo.py` · `call_trace_demo.py` | `manager_ai_core/`(바로 아래) | 라우팅→C1→C2→게이트→C3를 통합하는 MAC 오케스트레이터라 하위 컴포넌트 어디에도 속하지 않음 |
| `graph_inference/README.md` · `CLAUDE.md` | 위 4개 `CLAUDE.md`에 절 단위로 흡수 | 파일이 흩어졌으므로 실행법·의존성·캐비어트도 각 자리로 분산 |

축 라우팅(임베딩)은 원래 `end_to_end_pipeline.py`·`onto_axes.py`(준상님의 별도 저장소
`DATAS/`)를 통째로 임포트했는데, 그 파일들이 `multi_axis_coordination.py`·
`device_calling_pipeline.py`라는 **별개의 JSON-registry 기반 프로토타입 파이프라인**까지
끌고 왔다(이 폴더는 그걸 안 쓴다). 라우팅에 실제로 쓰는 부분(`ONTO_AXES`, `get_axis_scores`,
`THRESHOLD`, `USING_REAL_EMBEDDINGS`)만 `kg_mapping/axis_routing.py`로 새로 추출했고,
`axis_centroids.json`(축별 ko-sroberta 임베딩 중심값, 51KB)도 함께 저장소에 들여왔다 —
이제 이 저장소만으로 실행된다(예전엔 `DATAS/`와 같은 폴더에 있어야 돌았다).

## 승격하지 않은 것

- **`SOT.md` §2 트리는 바꾸지 않았다.** `kg_mapping/`·`policy_generation/`는 이미 정본
  구조에 있어서 새 디렉터리가 필요 없었다 — `sot_audit.py` 재실행 대상 아님.
- **IF-1 위반은 그대로 남겨뒀다.** `graph_retrieval.py`는 여전히 Neo4j를 직접 연다
  (HG-5 위반, 실험 코드라 의도적으로 보류). 정본으로 승격하려면 IF-1 어댑터가 필요하다.
- **Neo4j ↔ 기존 JSON KG(D-6)의 관계는 여전히 TODO(확인 필요)** — 이 변경은 배치만
  바꿨고 그 질문에 답하지 않는다.
- 실제 동작 검증: 로컬 Neo4j(`bolt://localhost:7687`)에 붙여 `pipeline.py`·`trace_demo.py`·
  `call_trace_demo.py`·`kg_mapping/graph_retrieval.py`·`policy_generation/rule_evaluator.py`·
  `kg_mapping/axis_routing.py`를 각각 실행해 5개 시나리오(WellBeing 발화/비발화, Safety,
  Comfort, OOS)가 이동 전과 같은 결과를 내는 것을 확인했다(1회 실측, `LLM_BACKEND=mock`).
