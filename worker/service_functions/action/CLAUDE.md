# Action Function (AF)

> **SOT**: `docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md`
> **상위**: `worker/service_functions/` · **Phase**: 0 · **구현 상태**: 구현됨 — 단일 웨이포인트만 검증

결정에 따른 물리 행동. 세션 키 검증 후 디바이스를 제어한다.

**파일**: `Actions.py` — `ActionModule(node, nav_action="navigate_to_pose")`
Nav2 `NavigateToPose` 액션 클라이언트를 감싸 웨이포인트 리스트를 백그라운드 스레드로 순차 전송한다.

## ROS2 의존 표면 (전부)

```python
from action_msgs.msg  import GoalStatus
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action  import NavigateToPose
```

**로봇 비의존이다.** Nav2만 돌면 turtlebot3든 실물 LIMO든 수정 없이 동작한다.

## 검증 실적 (과신 금지)

기록된 검증은 `plan_and_navigate(x=1.0, y=0.0)` **단일 웨이포인트 1회**뿐이다
(`sequence_result: {"completed": 1, "total": 1}`, `/odom` `(0,0)` → `(0.764, 0.009)`).
**다중 웨이포인트 순차 이동 · `cancel_goal_sequence` · `cancel`은 실행 기록이 없다.**
게다가 이 검증은 `turtlebot3_world`에서 이뤄졌고 **small_house 재검증은 없다.**

## ⚠️ G-5 — stale 콜백 가드 없음

- `_on_result`가 토큰 검사 없이 `self.status`를 덮어쓴다
- `cancel_goal`이 Nav2 취소 승인을 안 기다리고 낙관적으로 `"cancelled"`로 쓴다
- `_on_feedback`도 무조건 `"navigating"`을 쓴다 → stale feedback이 대기 루프를 풀 수 있다

**0-12**: `_goal_token` 도입 + 취소 승인 대기. (limo_slam이 같은 버그를 고친 전례가 있다)

## ⚠️ G-4 — `look_around` / patrol 미구현

`tools/scenarios/check_obj_state.json`이 `look_around`·`is_looking_around`·`interrupt_look_around`를
참조하지만 여기에 없다. **해당 시나리오는 실행 불가.**
(두 번째 실행 불가 사유도 있다 — `check_object_state`에 `detections` 인자를 넘기는데 RF가 받지 않는다)

## 주의

첫 웨이포인트는 `prev_xy`가 없어 `yaw_deg = 0.0`으로 떨어진다.
**현재 로봇 자세를 읽지 않으므로** 필요하면 명시적으로 줄 것.
