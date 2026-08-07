"""limo-MCP 맵 위에서 순찰 시나리오를 기하학적으로 시뮬레이션한다.

Gazebo 물리도 Nav2도 YOLO도 없이, 우리가 설계한 5단계 흐름을 그대로 재현:
  ① 순서 결정  ② 경로계획(A*)  ③ 1Hz 카메라 스캔
  ④ 경로 추종 이동          ④.5 도착 후 look_around 360° 회전
검증 목표: "이 순찰로 집 안 어디에 계신 할머니를 찾을 수 있는가" (커버리지)
"""
import cv2, numpy as np, os, math, heapq, json, re

D = os.path.dirname(os.path.abspath(__file__))

def _map_meta(path):
    """map.yaml 에서 해상도·원점을 읽는다.

    F-18 — 예전에는 같은 값이 이 파일과 patrol_viz.py 에 하드코딩돼 있고 map.yaml 은
    아무도 읽지 않았다. 맵을 교체하면 yaml 만 갱신되고 코드는 조용히 옛 원점으로
    계산해 커버리지 수치가 틀린 채로 나온다.
    """
    res = ox = oy = None
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("resolution:"):
                res = float(line.split(":", 1)[1])
            elif line.startswith("origin:"):
                nums = [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?", line)]
                ox, oy = nums[0], nums[1]
    if res is None or ox is None:
        raise SystemExit(f"map.yaml 에서 resolution/origin 을 못 읽었다: {path}")
    return res, ox, oy


RES, OX, OY = _map_meta(os.path.join(D, "maps", "map.yaml"))   # 정본은 map.yaml (F-18)

# --- 로봇/센서 제원 (turtlebot3 waffle 기준, LIMO도 유사) ---
V_LIN      = 0.22      # m/s
V_ANG      = 0.50      # rad/s
ROBOT_R    = 0.22      # m (충돌 여유)
CAM_FOV    = math.radians(62)   # realsense r200 수평 화각
CAM_RANGE  = 4.0       # m, 사람 검출 유효 거리
SCAN_HZ    = 1.0
N_RAYS     = 48        # 가시영역 계산용 레이 수

SPAWN = (3.5, 1.0, 0.0)
# 사각지대 2곳((-7.77,0.56) 좌상단 방, (8.10,1.71) 식탁구역)을 추가하고
# 이동거리가 짧아지도록 시계방향 루프로 재배열
PATROL = [(8.10, 1.71), (4.30, -0.55), (1.45, 4.35), (-2.00, -0.80),
          (-7.77, 0.56), (-7.90, -2.95), (7.15, -3.30)]

# ---------- 맵 ----------
with open(os.path.join(D, "maps", "map.pgm"), "rb") as f:
    img = cv2.imdecode(np.frombuffer(f.read(), np.uint8), cv2.IMREAD_GRAYSCALE)
H, W = img.shape
free = (img > 250).astype(np.uint8)                 # 자유공간
blocked = (img < 250).astype(np.uint8)              # 벽 + 미탐색 = 시야 차단
dist_m = cv2.distanceTransform(free, cv2.DIST_L2, 5) * RES
drivable = dist_m >= ROBOT_R                        # 로봇 중심이 갈 수 있는 곳

def to_px(x, y):  return int(round((x - OX) / RES)), int(round(H - (y - OY) / RES))
def to_m(px, py): return OX + px * RES, OY + (H - py) * RES

# ---------- A* ----------
def astar(start_m, goal_m):
    s, g = to_px(*start_m), to_px(*goal_m)
    def snap(p):                                     # 가까운 주행가능 셀로 스냅
        if drivable[p[1], p[0]]: return p
        ys, xs = np.nonzero(drivable)
        k = np.argmin((xs - p[0])**2 + (ys - p[1])**2)
        return int(xs[k]), int(ys[k])
    s, g = snap(s), snap(g)
    nbr = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]
    openq = [(0.0, s)]; came = {}; gs = {s: 0.0}
    while openq:
        _, cur = heapq.heappop(openq)
        if cur == g: break
        for dx, dy in nbr:
            nx, ny = cur[0]+dx, cur[1]+dy
            if not (0 <= nx < W and 0 <= ny < H) or not drivable[ny, nx]: continue
            step = math.hypot(dx, dy)
            # 벽에 붙지 않도록 여유가 적은 셀에 페널티
            cost = gs[cur] + step * (1.0 + 2.0 * max(0.0, 0.6 - dist_m[ny, nx]))
            if cost < gs.get((nx, ny), 1e18):
                gs[(nx, ny)] = cost; came[(nx, ny)] = cur
                h = math.hypot(nx-g[0], ny-g[1])
                heapq.heappush(openq, (cost + h, (nx, ny)))
    if g not in came and g != s: return None
    path, c = [], g
    while c != s:
        path.append(to_m(*c)); c = came[c]
    path.append(to_m(*s)); path.reverse()
    return path[::4]                                  # 0.2m 간격으로 솎기

# ---------- 가시영역 ----------
cover = np.zeros((H, W), np.uint8)
def mark_visible(x, y, yaw):
    cx, cy = to_px(x, y)
    for i in range(N_RAYS):
        a = yaw - CAM_FOV/2 + CAM_FOV * i / (N_RAYS - 1)
        dx, dy = math.cos(a), -math.sin(a)
        for step in range(1, int(CAM_RANGE / RES)):
            px, py = int(cx + dx*step), int(cy + dy*step)
            if not (0 <= px < W and 0 <= py < H) or blocked[py, px]: break
            cover[py, px] = 1

# ---------- 순찰 실행 ----------
t = 0.0
next_scan = 0.0
x, y, yaw = SPAWN
log, scans, traj = [], [], [(x, y)]

def advance_to(nx, ny):
    """직선 구간을 이동하며 1Hz로 스캔."""
    global x, y, yaw, t, next_scan
    tgt = math.atan2(ny - y, nx - x)
    dyaw = (tgt - yaw + math.pi) % (2*math.pi) - math.pi
    for phase, dur in (("turn", abs(dyaw)/V_ANG), ("move", math.hypot(nx-x, ny-y)/V_LIN)):
        t0, y0, x0, yaw0 = t, y, x, yaw
        while t < t0 + dur:
            dt = min(0.1, t0 + dur - t); t += dt
            f = (t - t0) / dur if dur > 0 else 1.0
            if phase == "turn": yaw = yaw0 + dyaw * f
            else: x, y = x0 + (nx-x0)*f, y0 + (ny-y0)*f
            if t >= next_scan:
                mark_visible(x, y, yaw); scans.append((x, y, yaw, t)); next_scan += 1.0/SCAN_HZ
        yaw = yaw0 + dyaw if phase == "turn" else yaw
        x, y = (nx, ny) if phase == "move" else (x, y)
    traj.append((x, y))

def look_around():
    global yaw, t, next_scan
    dur = 2*math.pi / V_ANG
    t0, yaw0 = t, yaw
    while t < t0 + dur:
        dt = min(0.1, t0 + dur - t); t += dt
        yaw = yaw0 + 2*math.pi * (t - t0)/dur
        if t >= next_scan:
            mark_visible(x, y, yaw); scans.append((x, y, yaw, t)); next_scan += 1.0/SCAN_HZ

print(f"맵 {W}x{H} px = {W*RES:.1f}x{H*RES:.1f} m,  자유공간 {free.sum()*RES*RES:.0f} m2")
print(f"로봇 v={V_LIN} m/s, w={V_ANG} rad/s, FOV {math.degrees(CAM_FOV):.0f}°, 사거리 {CAM_RANGE} m, 스캔 {SCAN_HZ} Hz\n")
print(f"{'구간':<22}{'거리(m)':>9}{'누적시간':>10}{'스캔':>7}{'커버율':>9}")
print("-" * 60)

mark_visible(x, y, yaw)
prev = (x, y)
for i, (gx, gy) in enumerate(PATROL, 1):
    path = astar((x, y), (gx, gy))
    if path is None:
        print(f"  WP{i} ({gx},{gy}) : ❌ 경로 없음"); continue
    d0 = t; s0 = len(scans); px0, py0 = x, y
    for wx, wy in path[1:]:
        advance_to(wx, wy)
    dist_travelled = sum(math.hypot(path[k+1][0]-path[k][0], path[k+1][1]-path[k][1])
                         for k in range(len(path)-1))
    print(f"{'이동 -> WP'+str(i):<22}{dist_travelled:>9.1f}{t:>9.0f}s{len(scans)-s0:>7}"
          f"{100*cover.sum()/free.sum():>8.1f}%")
    s1 = len(scans)
    look_around()
    print(f"{'  look_around WP'+str(i):<22}{'-':>9}{t:>9.0f}s{len(scans)-s1:>7}"
          f"{100*cover.sum()/free.sum():>8.1f}%")

covered = int((cover & free).sum())
total = int(free.sum())
print("-" * 60)
print(f"총 소요 {t:.0f}초 ({t/60:.1f}분),  스캔 {len(scans)}회")
print(f"커버리지 {covered}/{total} = {100*covered/total:.1f}%  (미커버 {(total-covered)*RES*RES:.1f} m2)")

# ---------- 미커버 영역 ----------
uncov = (free & ~cover).astype(np.uint8)
n, lbl, st, cent = cv2.connectedComponentsWithStats(uncov, 8)
big = sorted([(st[i, cv2.CC_STAT_AREA]*RES*RES, i) for i in range(1, n)], reverse=True)
print("\n미커버 영역 상위 (2 m2 이상):")
for a, i in big[:6]:
    if a < 2.0: break
    cx, cy = cent[i]
    print(f"  {a:5.1f} m2  중심 ({OX+cx*RES:6.2f}, {OY+(H-cy)*RES:6.2f})")

# ---------- 시각화 ----------
vis = np.full((H, W, 3), 60, np.uint8)
vis[free > 0] = (235, 235, 235)
vis[(cover & free) > 0] = (170, 235, 170)      # 커버된 자유공간 = 연두
vis[img < 100] = (30, 30, 30)                  # 벽
for k in range(len(traj)-1):
    cv2.line(vis, to_px(*traj[k]), to_px(*traj[k+1]), (200, 80, 0), 1)
for sx, sy, syaw, _ in scans:
    cv2.circle(vis, to_px(sx, sy), 1, (0, 0, 200), -1)
for i, (gx, gy) in enumerate(PATROL, 1):
    p = to_px(gx, gy)
    cv2.circle(vis, p, 6, (0, 0, 220), -1)
    cv2.putText(vis, str(i), (p[0]+8, p[1]+4), cv2.FONT_HERSHEY_SIMPLEX, .5, (0,0,220), 2)
sp = to_px(SPAWN[0], SPAWN[1])
cv2.circle(vis, sp, 7, (0, 160, 255), 2)
cv2.putText(vis, "S", (sp[0]-4, sp[1]+4), cv2.FONT_HERSHEY_SIMPLEX, .5, (0,160,255), 2)

ys, xs = np.nonzero(free)
crop = vis[ys.min()-8:ys.max()+8, xs.min()-8:xs.max()+8]
out = cv2.resize(crop, None, fx=3, fy=3, interpolation=cv2.INTER_NEAREST)
cv2.imencode(".png", out)[1].tofile(os.path.join(D, "patrol_sim.png"))
print("\nsaved patrol_sim.png  (연두=카메라가 본 영역, 주황선=주행 경로, 빨간점=스캔 위치)")
