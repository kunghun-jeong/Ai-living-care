"""임의의 시나리오 JSON(scenario_id/input/steps 스키마)을 MCP_server.py에 대해 실행하는 범용 실행기.

docs/api-spec.md·WORLD.md가 반복해서 지적해 온 갭 — "이 JSON DSL을 해석하는 실행기가
저장소에 없다" — 을 메운다. Scenarios/*.json이 이 스키마를 따르기만 하면 별도 코드 없이
그대로 실행된다 (turn_on_air_conditioner.json·check_obj_state.json 기준으로 문법을 맞췄다).

지원하는 step type:
  call             — tool 하나를 호출하고 결과를 이 step id에 저장한다
  branch           — condition(점 경로, "$" 없음)을 진리값으로 평가해 on_true/on_false로 분기
  poll_until_match — timeout까지 tool을 반복 호출하며 match 조건을 확인한다

참조 문법 (args 안에서만 "$" 접두):
  $input.<path>        — 시나리오 input 블록
  $<step_id>.<path>     — 앞선 step의 결과 (점으로 중첩 접근, 리스트 인덱스도 가능)
branch의 condition은 "$" 없이 "<step_id>.<path>" 그대로 쓴다 (check_obj_state.json 관례).

next/on_true/on_false 생략 시 배열의 다음 step으로 넘어가고, 마지막 step이면 "success"로
끝난다. "success"/"fail"은 실제 step이 아니라 종료 sentinel이다 ("fail"은 최상위 fail 블록을
결과에 싣는다).

match 두 형식을 모두 지원한다:
  {"field": "status", "equals": "succeeded"}                              — 단순 값 비교
  {"field": "detections", "class_field": "class", "target": "$input.x"}   — 리스트 멤버십

사용:
    source /opt/ros/jazzy/setup.bash
    cd limo-MCP
    python3 Scenarios/run_scenario.py Scenarios/turn_on_air_conditioner.json
"""

import asyncio
import json
import os
import sys
import time


def _get_path(obj, path: str):
    """"a.b.0.c" 점 경로로 dict/list를 따라 들어간다. 못 찾으면 None."""
    if not path:
        return obj
    cur = obj
    for part in path.split("."):
        if isinstance(cur, list):
            try:
                cur = cur[int(part)]
            except (ValueError, IndexError):
                return None
        elif isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
        if cur is None:
            return None
    return cur


class ScenarioRunner:
    """시나리오 하나를 세션 하나에 대해 실행한다. MCP 세션은 밖에서 주입받는다."""

    def __init__(self, session, scenario: dict, log=print):
        self.session = session
        self.scenario = scenario
        self.log = log
        self.results: dict = {"input": scenario.get("input", {})}
        self._order = [s["id"] for s in scenario["steps"]]
        self._by_id = {s["id"]: s for s in scenario["steps"]}

    def _resolve(self, value):
        """"$input.x" / "$step_id.field" 참조를 값 안에서 재귀적으로 치환한다."""
        if isinstance(value, str) and value.startswith("$"):
            step_id, _, path = value[1:].partition(".")
            return _get_path(self.results.get(step_id), path)
        if isinstance(value, dict):
            return {k: self._resolve(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._resolve(v) for v in value]
        return value

    def _resolve_condition(self, condition: str):
        step_id, _, path = condition.partition(".")
        return _get_path(self.results.get(step_id), path)

    async def _call_tool(self, tool: str, args: dict) -> dict:
        resolved_args = self._resolve(args or {})
        try:
            result = await self.session.call_tool(tool, resolved_args)
        except Exception as exc:  # noqa: BLE001 — 존재하지 않는 tool 등, 결과로 감싸 계속 진행
            return {"_error": f"{tool}({resolved_args}) 호출 실패: {exc!r}"}
        if getattr(result, "isError", False):
            text = result.content[0].text if result.content else str(result)
            return {"_error": text}
        text = result.content[0].text if result.content else "{}"
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"_raw": text}

    def _check_match(self, result: dict, match: dict) -> bool:
        if not match:
            return True
        if "equals" in match:
            return result.get(match["field"]) == match["equals"]
        if "class_field" in match:
            # target 을 실제로 대조한다. 이걸 빠뜨리면 의자를 검출해도 "사람 찾음"이 된다.
            target = self._resolve(match.get("target"))
            items = result.get(match["field"]) or []
            if target is None:
                return any(item.get(match["class_field"]) for item in items)
            return any(item.get(match["class_field"]) == target for item in items)
        return False

    def _default_next(self, step_id: str) -> str:
        idx = self._order.index(step_id)
        return self._order[idx + 1] if idx + 1 < len(self._order) else "success"

    async def _run_step(self, step: dict) -> str:
        step_id, step_type = step["id"], step["type"]
        default_next = self._default_next(step_id)
        self.log(f"  [{step_id}] {step_type}" + (f" -> {step['tool']}" if "tool" in step else ""))

        if step_type == "call":
            out = await self._call_tool(step["tool"], step.get("args", {}))
            self.results[step_id] = out
            self.log(f"      {out}")
            return step.get("next", default_next)

        if step_type == "branch":
            cond = self._resolve_condition(step["condition"])
            branch = "on_true" if cond else "on_false"
            self.log(f"      condition({step['condition']})={cond!r} -> {step[branch]}")
            return step[branch]

        if step_type == "poll_until_match":
            deadline = time.monotonic() + step.get("timeout", 30.0)
            interval = step.get("poll_interval", 1.0)
            match = step.get("match")
            stop_when = step.get("stop_when")
            last: dict = {}
            while time.monotonic() < deadline:
                last = await self._call_tool(step["tool"], step.get("args", {}))
                if self._check_match(last, match):
                    interrupt = step.get("interrupt")
                    if interrupt:
                        # 찾았으면 진행 중인 동작을 세운다 (check_obj_state.json 관례).
                        stop = await self._call_tool(interrupt["tool"], interrupt.get("args", {}))
                        self.log(f"      interrupt {interrupt['tool']}: {stop}")
                    self.results[step_id] = {**last, "matched": True}
                    self.log(f"      matched: {last}")
                    return step.get("next", default_next)
                if stop_when:
                    stop_result = (
                        last
                        if stop_when.get("tool") == step["tool"]
                        else await self._call_tool(stop_when["tool"], {})
                    )
                    if stop_result.get(stop_when["field"]) == stop_when["equals"]:
                        break
                await asyncio.sleep(interval)
            self.results[step_id] = {**last, "matched": False}
            self.log(f"      no match (timeout/stop_when): {last}")
            return step.get("next", default_next)

        raise ValueError(f"unknown step type: {step_type!r}")

    async def run(self) -> dict:
        cur_id = self._order[0]
        while True:
            if cur_id == "success":
                self.log("RESULT: success")
                return {"outcome": "success", "results": self.results}
            if cur_id == "fail":
                fail_info = self.scenario.get("fail", {})
                self.log(f"RESULT: fail — {fail_info}")
                return {"outcome": "fail", "reason": fail_info, "results": self.results}
            step = self._by_id.get(cur_id)
            if step is None:
                raise ValueError(f"unknown step id referenced: {cur_id!r}")
            cur_id = await self._run_step(step)


async def _main(scenario_path: str) -> int:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    with open(scenario_path, encoding="utf-8") as f:
        scenario = json.load(f)

    print(f"=== {scenario['scenario_id']} ===")
    print(f"input: {scenario.get('input', {})}\n")

    server_path = os.path.join(os.path.dirname(__file__), "..", "MCP_server", "MCP_server.py")
    params = StdioServerParameters(command="python3", args=[server_path], env=dict(os.environ))
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            outcome = await ScenarioRunner(session, scenario).run()
            return 0 if outcome["outcome"] == "success" else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"usage: python3 {sys.argv[0]} <scenario.json>")
        sys.exit(1)
    sys.exit(asyncio.run(_main(sys.argv[1])))
