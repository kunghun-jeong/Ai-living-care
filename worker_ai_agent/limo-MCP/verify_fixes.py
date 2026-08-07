#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""수정한 안전 경로를 실제로 실행해 확인한다 (하네스 「실패 경로를 한 번 실행」).

ROS2 없이 돈다 — Reasonings.py 는 의존성 주입이고, Actions.py 의 검증 함수는 순수 함수다.
"""
import os, sys, time, types

W = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Worker_functions")
sys.path.insert(0, W)

ok = fail = 0
def t(name, cond, detail=""):
    global ok, fail
    if cond: ok += 1; print(f"  PASS  {name}")
    else:    fail += 1; print(f"  FAIL  {name}   {detail}")

from Reasonings import ReasoningModule, PersonScan

# ── F-47 · 증거 이미지 신뢰도 하한 ────────────────────────────────────────────
print("\n[F-47] 증거 이미지 신뢰도 하한")
FRAME = {"frame_id": "f_1", "frame": object(), "stamp": 1.0, "pose": None, "age_sec": 0.1}

def src(fid=None): return FRAME
def crop_ok(_f, _b): return b"JPEG"

r = ReasoningModule(detect_fn=lambda f: [{"class": "person", "conf": 0.08, "bbox": [0, 0, 10, 10]}],
                    crop_fn=crop_ok, frame_source=src)
out = r.check_object_state("person")
t("conf 0.08 오탐은 증거로 안 올라간다", out["image_jpeg"] is None and "confidence" in out["reason"], out)

r = ReasoningModule(detect_fn=lambda f: [{"class": "person", "conf": 0.91, "bbox": [0, 0, 10, 10]}],
                    crop_fn=crop_ok, frame_source=src)
out = r.check_object_state("person")
t("conf 0.91 은 증거로 올라간다", out["image_jpeg"] == b"JPEG", out)

r = ReasoningModule(detect_fn=lambda f: [{"class": "person", "conf": 0.91, "bbox": None}],
                    crop_fn=lambda _f, _b: None, frame_source=src)
out = r.check_object_state("person")
t("크롭 실패 시 전체 프레임으로 조용히 대체하지 않는다",
  out["image_jpeg"] is None and "crop failed" in out["reason"], out)

def src_none(fid=None): return None
r = ReasoningModule(detect_fn=lambda f: [], crop_fn=crop_ok, frame_source=src_none)
out = r.check_object_state("person")
t("프레임 없음(=stale 포함)이 사유로 구분된다", "no fresh frame" in out["reason"], out)

# ── F-50 · 멈춘 스캔이 사람을 「발견」하지 않는다 ─────────────────────────────
print("\n[F-50] 정지한 스캔의 결과 기록")
seq = {"n": 0}
def moving_src(fid=None):
    seq["n"] += 1
    return {"frame_id": f"f_{seq['n']}", "frame": object(), "stamp": 0.0, "pose": None}

def slow_detect(_f):
    time.sleep(0.25)                       # 추론 중에 stop() 이 들어오는 상황
    return [{"class": "person", "conf": 0.9, "bbox": [0, 0, 5, 5]}]

s = PersonScan("t1", moving_src, slow_detect, hz=20.0, stop_on_hit=False)
s.start(); time.sleep(0.05); s.stop(); time.sleep(0.5)
t("stop() 이후 found 가 true 로 뒤집히지 않는다", s.status()["found"] is False, s.status())

# ── F-50b · 재요청 파라미터를 조용히 버리지 않는다 ───────────────────────────
print("\n[F-50b] 스캔 재요청 파라미터")
r = ReasoningModule(detect_fn=lambda f: [], frame_source=moving_src)
first = r.start_person_scan(hz=1.0, min_conf=0.5, stop_on_hit=False)
second = r.start_person_scan(hz=5.0, min_conf=0.3, stop_on_hit=False)
t("첫 시작은 started=True", first.get("started") is True, first)
t("재요청은 started=False + 미적용을 명시", second.get("started") is False and "NOT applied" in second.get("reason", ""), second)
t("실제 적용 중인 값을 알려준다", second.get("active_min_conf") == 0.5, second)
r.stop_person_scan()

# ── F-51 · 죽은 카메라를 「사람 없음 확정」으로 읽지 않는다 ───────────────────
print("\n[F-51] 새 프레임 0장일 때의 결론")
STUCK = {"frame_id": "same", "frame": object(), "stamp": 0.0, "pose": None}
s = PersonScan("t2", lambda fid=None: STUCK, lambda f: [], hz=50.0, stop_on_hit=False)
s.start(); time.sleep(0.3); s.stop(); time.sleep(0.1)
st = s.status()
t("카메라가 멈추면 conclusive=False", st["found"] is False and st["conclusive"] is False, st)
t("사유가 붙는다", "cannot conclude" in st.get("reason", ""), st)
t("no_frame_ticks 가 센다", st["no_frame_ticks"] > 0, st)

s = PersonScan("t2b", lambda fid=None: None, lambda f: [], hz=50.0, stop_on_hit=False)
s.start(); time.sleep(0.2); s.stop(); time.sleep(0.1)
st = s.status()
t("프레임을 한 장도 못 받으면 conclusive=False",
  st["frames_seen"] == 0 and st["conclusive"] is False, st)

s = PersonScan("t3", moving_src, lambda f: [], hz=50.0, stop_on_hit=False)
s.start(); time.sleep(0.3); s.stop(); time.sleep(0.1)
st = s.status()
t("프레임을 봤고 사람이 없으면 conclusive=True", st["found"] is False and st["conclusive"] is True, st)

# ── F-4 · 웨이포인트 입력 검증 (Actions.py 순수 함수) ────────────────────────
print("\n[F-4] 웨이포인트 입력 검증")
for name in ("action_msgs.msg", "geometry_msgs.msg", "nav2_msgs.action", "rclpy.action", "rclpy"):
    m = types.ModuleType(name)
    for attr in ("GoalStatus", "PoseStamped", "NavigateToPose", "ActionClient"):
        setattr(m, attr, type(attr, (), {}))
    sys.modules.setdefault(name.split(".")[0], types.ModuleType(name.split(".")[0]))
    sys.modules[name] = m
from Actions import validate_waypoints, _goal_xy_yaw

t("정수 좌표를 받아들이고 float 로 바꾼다", validate_waypoints([(1, 0)]) is None)
t("float 변환 확인", isinstance(_goal_xy_yaw((1, 0))[0], float))
t("빈 리스트 거부", validate_waypoints([]) == "empty waypoint list")
t("리스트가 아니면 거부", "must be a list" in (validate_waypoints("1.0,0.0") or ""))
t("문자 좌표 거부", "non-numeric" in (validate_waypoints([{"x": "a", "y": 0}]) or ""))
t("x 누락 거부", "missing" in (validate_waypoints([{"y": 0}]) or ""))
t("NaN 거부", "NaN" in (validate_waypoints([(float("nan"), 0)]) or ""))
t("좌표 1개짜리 거부", "at least" in (validate_waypoints([(1,)]) or ""))

print(f"\n{'='*54}\n  {ok} PASS / {fail} FAIL\n{'='*54}")
sys.exit(1 if fail else 0)
