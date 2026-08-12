# 2026-08-12 · clean_room.json에 가상 진공청소기 IR 신호를 추가한다

## 무엇

`clean_room.json`의 각 구역 진입/이탈 시점에 `send_ir_signal(device="vacuum",
command="clean_start"/"clean_stop")`을 추가했다(100 → 112 step). 구역의 첫 leg
(`r{n}_l1_resolve`) 직전에 `clean_start`, 마지막 leg(`r{n}_l4_arrive`) 직후·다음 구역
이동 전에 `clean_stop`이 들어간다.

## 왜, 그리고 이게 왜 조심스러운가

`clean_room.json` 초판(`docs/decisions/2026-08-12-room-cleaning-scenario.md`)은 좌우 스윕
**이동 패턴 자체**로 청소를 표현했다 — LIMO의 MCP tool 16종에 청소 액추에이터가 없고
`entities.json`/`small_house.world`에도 진공청소 장치가 없어서였다. 실행해서 확인한
사용자가 "청소를 안 하는 것 같다"고 지적했다 — 맞는 지적이다, 움직임 말고는 청소를
나타내는 게 아무것도 없었다.

**LIMO에 진공청소 부착물이 실제로 달려 있다고 가정하고** 가상 IR 신호를 넣기로 사용자와
합의했다. **이건 사실이 아니라 가정이다** — `entities.json`에 `vacuum` 디바이스를 등록하지
않은 이유이기도 하다(다른 device 엔티티는 전부 실존하는 좌표 있는 장치인데, `vacuum`은
로봇에 붙어 있어 좌표가 없고 애초에 실존 여부가 확인된 적 없다). `send_ir_signal` 자체도
스텁(`MCP_server.py` — "실제 송신 하드웨어는 미구현, 로그만 남긴다")이라 이 신호는
**로그 한 줄 이상의 의미가 없다.** 실물 로봇에 진공 하드웨어가 실제로 붙으면 그때
`device_class`·좌표(로봇 좌표계 기준 오프셋)를 `entities.json`에 정식으로 등록해야 한다.

## 정본 반영

`worker_ai_agent/limo-MCP/CLAUDE.md`에 파일 추가 한 줄. `clean_room.json`의 `note`
필드에도 이 가정을 명시했다.

## 검증

```
python3 Scenarios/validate_variant.py Scenarios/clean_room.json   # 구조 검증 PASS, 112 step
```

RViz2/MCP로 실제 실행해 `clean_start`/`clean_stop` 로그가 각 구역 경계에서 찍히는지는
사용자가 WSL 환경에서 확인 중 — 이 문서 작성 시점에는 아직 결과를 못 받았다
(TODO 확인 필요).
