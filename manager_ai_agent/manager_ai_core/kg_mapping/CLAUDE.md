# KG Mapping

> **역할** 어구 → KG element=value 바인딩. IF-1 경유만
> **상태** Phase 0 · 미착수(정본 IF-1 바인딩) · 갭 `G-6` · **실험 코드 있음(아래, 미승인)**
> **읽을 절** spec **§3.1**(IF-1 계약) · **§4.2** — 그 외 절은 열지 않는다
> **정본** 구조 `SOT.md` · spec §3.1

추출된 어구를 KG에 조회해 `element = value` 바인딩으로 해소한다. **IF-1 경유** (`interfaces/if01_database/`).

```
resolve(phrase: str, context: dict) -> list[Binding]
Binding = {"element": str, "value": any, "confidence": float, "source": str}
```

slide 21의 KG mapping 표:

| PHRASE | ELEMENT → RETRIEVED VALUE |
|---|---|
| "Grandma" | `target = elder`, `place = living_room` |
| "check" | `task = safety_check`, `mobile = [LIMO_1, LIMO_2]` |
| "is okay" | `condition = realtime`, `sensor = camera` |

## 주의

- **KG를 직접 파일로 읽지 말 것.** IF-1 계약으로만 접근해야 후일 그래프DB로 무중단 교체할 수 있다 (D-6).
- `confidence`를 반드시 채운다. 낮은 신뢰도 바인딩은 사용자 확인(MRTR)으로 승격될 수 있다.

## 실험 코드 — `graph_retrieval.py` · `axis_routing.py` (실험 · 미승인)

2026-08-18에 옛 `manager_ai_agent/graph_inference/`를 폐기하고 여기로 옮겼다
(`docs/decisions/2026-08-18-graph-inference-distribution.md`).

- `graph_retrieval.py` — Neo4j를 **직접** 열어 조회한다 (`GraphDatabase.driver(...)`).
  **위 HG-5("KG를 직접 읽지 않는가")를 문자 그대로 어긴다** — IF-1 `resolve()` 계약을
  거치지 않는다. 실험 단계라 남겨두지만, 정본으로 승격하려면 IF-1 어댑터로 감싸야 한다.
- `axis_routing.py` — 자연어를 어구로 쪼개는 대신 **축(axis) 단위**로 라우팅한다
  (`onto:saref/WellBeing` 등). slide 21의 phrase 기반 매핑과 **입도가 다르다.**
- `axis_centroids.json` — `axis_routing.py`의 진짜 임베딩 모드가 쓰는 축별 중심값
  (`jhgan/ko-sroberta-multitask`). 없어도 단어겹침 폴백으로 동작한다.

### 기존 KG와의 관계 — TODO(확인 필요)

- 이 저장소의 정본 KG는 **JSON 룩업**이다 — `../../knowledge_graph/entities.json`,
  결정 **D-6**("KG는 그래프DB가 아니라 JSON"). `graph_retrieval.py`는 **Neo4j**를 쓴다.
- 스키마도 다르다 — 여기는 `Axis/Device/Function/State/AxisKnowledge`,
  `knowledge_graph/`의 정본은 `person/space/device`(grandma·living_room·LIMO_1).
- **Neo4j 채택 여부 · JSON KG와의 관계(대체/공존) · "DB 없음" 원칙과의 정합성**은
  전부 팀 논의 대기다. 임의로 정본으로 단정하지 않는다.

### 의존성

`GraphRetriever`가 붙는 그래프(`livingcare_graph_v2.cypher`로 구축)는 **이 저장소 밖**
(준상님 소유)에 있다. `NEO4J_PASSWORD` 환경변수로 접속 비밀번호를 넘긴다 — 코드 기본값은
예시일 뿐이다. 실행법은 `../CLAUDE.md`의 「Neo4j 추론 파이프라인」참조.

### 비밀번호 — `.env`(로컬 전용, git에 안 올라감)

Windows `setx`로 시스템 환경변수를 바꿔도 **이미 열려 있는 터미널·IDE에는 반영되지 않는다**
(레지스트리만 바뀌고 살아있는 프로세스는 예전 환경을 그대로 물려받는다). 그래서
`graph_retrieval.py`는 import 시점에 이 폴더의 `.env`(`KEY=VALUE` 한 줄씩, `.gitignore`
등재됨)를 직접 읽어 `os.environ`에 채운다 — 이미 설정된 환경변수는 덮어쓰지 않는다.
새로 접속 정보를 바꾸려면 이 폴더의 `.env`를 고치거나 `NEO4J_PASSWORD` 환경변수를 쓴다.
