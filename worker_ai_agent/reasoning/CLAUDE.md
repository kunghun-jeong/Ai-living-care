# Reasoning Function (RF)

> **구조 정본**: `SOT.md` · **설계 정본**: `docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md`
> **상위**: `worker_ai_agent/` · **Phase**: 0 · **구현 상태**: **구현 완성도 최고**

관측으로부터 상태를 판단한다. 정책 규칙·컨텍스트·디바이스 지식을 다룬다. IF-5 · IF-6.

**파일**: `Reasonings.py` — `ReasoningModule` + `PersonScan` + `yolo_detect`

## 왜 이 파일이 기준인가

**ROS2에 의존하지 않는 순수 로직**이다. 백엔드(YOLO·Nav2·크롭)를 생성자로 주입받고
미주입 시 no-op으로 동작하므로 **로봇 없이 단독 테스트가 가능하다.**
이 저장소에서 가장 잘 분리된 설계이므로 다른 컴포넌트를 만들 때 이 패턴을 따를 것.

```python
DetectFn    = Callable[[object], list]          # frame -> [{"class","conf","bbox"}]
PlanFn      = Callable[[dict, dict], list]      # start, goal -> [{"x","y","yaw"}]
CropFn      = Callable[[object, list], bytes]   # frame, bbox -> jpeg bytes
FrameSource = Callable[..., Optional[dict]]
```

## `PersonScan` — P-3의 "코드 자율 구간"

1 Hz로 최신 프레임에 YOLO를 돌려 **사람 유무(O/X)만** 판별한다. **상태 판정은 하지 않는다.**
사람이 잡히면 frame_id·pose·bbox만 기록하고, "괜찮은지"는 상위 LLM이 크롭 이미지를 보고 정한다.

**이 분리가 P-3의 실체다.** 픽셀이 LLM에 올라가는 유일한 순간은 `check_object_state`가 크롭 1장을
돌려줄 때다. 컨텍스트 보호와 비용 절감이 동시에 된다.

## ⚠️ G-3 — API 5종이 MCP tool로 미노출

`start_person_scan` · `wait_for_person` · `check_object_state` · `stop_person_scan` · `get_scan_status`가
**구현돼 있으나** `../mcp_server/MCP_server.py`에 tool 데코레이터가 없다.
시나리오 1의 탐색·판정 경로를 외부에서 호출할 수 없다. **구현이 아니라 노출만 하면 되는 저비용 작업 (0-9).**

## 주의

`yolo_detect`는 `ultralytics`를 **함수 안에서만 import**한다 — 이 모듈을 그냥 import했을 때
torch 등 무거운 의존성을 물지 않게 하기 위함이다. 이 lazy import를 최상단으로 올리지 말 것.
