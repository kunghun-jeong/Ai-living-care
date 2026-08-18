# Graph Inference (실험 · 미승인)

> **역할** 자연어 → 축 라우팅 → 그래프 조회(C1) → 규칙 판단(C2) → 로봇 intent 생성(C3) 추론 파이프라인
> **상태** 제안 · 리뷰 대기 · 로컬 동작 · Neo4j(준상 지식그래프) + ko-sroberta 임베딩 + 규칙엔진 + Ollama qwen2.5(무료) 로 · 센서 관측값은 mock(State 미연결)
> **정본** 미등재 — `SOT.md` 등재·`docs/decisions/` 반영은 **팀 승인 후** (TODO 확인 필요)

준상님의 Neo4j 지식그래프 위에 얹는 추론 계층. 자연어 한 문장("할머니 괜찮은지 확인해줘")을
로봇 실행 intent로 변환한다. **판단(위험도·에스컬레이션)은 코드가 규칙으로 결정**하고,
**LLM(Ollama/Claude)은 조립만** 한다. 그래프는 **읽기 전용(MATCH)** 으로만 접근한다.

## ⚠️ 기존 KG와의 관계 — TODO(확인 필요)

이 폴더는 **Neo4j(그래프DB)** 를 쓴다. 그러나:

- 이 저장소의 현재 KG는 **JSON 룩업**이다 — `../knowledge_graph/entities.json`,
  결정 **D-6**("KG는 그래프DB가 아니라 JSON"), README "DB 없음".
- 스키마도 다르다 — 여기는 `Axis/Device/Function/State/AxisKnowledge`,
  기존 KG는 `person/space/device`(grandma·living_room·LIMO_1).

따라서 **Neo4j 채택 여부 · 기존 JSON KG와의 관계(대체/공존) · "DB 없음" 원칙과의 정합성**은
전부 **TODO(확인 필요), 팀 논의 대기**다. 임의로 정본으로 단정하지 않는다.

> 참고: `knowledge_graph/CLAUDE.md`는 "후일 그래프DB로 무중단 교체", "Phase 1에서 그래프 순회 +
> 임베딩 유사도로 대체"를 예고한다. 이 폴더는 그 방향의 실험이나 **현재 결정 D-6(JSON)보다 앞서 있다.**

## 파일

| 파일 | 역할 |
|---|---|
| `graph_retrieval.py` | C1 — Neo4j 조회 (읽기 전용 Cypher) |
| `rule_evaluator.py` | C2 — 규칙 평가(판단, 코드) |
| `sequence_generator.py` | C3 — 로봇 intent 생성 (Ollama/Claude/mock) |
| `pipeline.py` | 통합 (라우팅→C1→C2→게이트→C3) |
| `trace_demo.py` · `call_trace_demo.py` | 학습용 데이터/함수호출 추적 데모 |
| `README.md` | 실행법·의존성·mock 현황·결정 대기 목록 |

## 의존성 (독립 실행 불가 — 준상 코드 필요)

이 코드는 준상님의 라우팅/그래프 파일들(`end_to_end_pipeline.py`, `onto_axes.py`,
`axis_centroids.json`, `livingcare_graph_v2.cypher`, `*_knowledge.py` 등)과 **Neo4j 인스턴스**가
있어야 돈다. 현재 그 파일들은 이 저장소에 없다 — `README.md` 참조. **이 폴더만으로는 실행되지 않는다.**

## 팀과 정할 것 (요약 · `README.md`에 상세)

- **State**: 누가 쓰나 / 원본값 vs 가공값 / key 규약 / 읽기 권한 / 센서별 유무·신선도
- **에스컬레이션**: `requires_escalation_from` 그래프化 여부 / phase 전환 기준 / 배터리 등 물리조건
- **아키텍처**: Neo4j vs 기존 JSON KG (위 「확인 필요」)
