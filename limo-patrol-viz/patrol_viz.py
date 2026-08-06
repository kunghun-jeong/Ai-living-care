#!/usr/bin/env python3
"""limo-MCP 맵 위에서 순찰 시나리오를 RViz2로 애니메이션한다.

Gazebo/Nav2 없이 A*로 경로를 뽑고 운동학만 적분해서 로봇을 실제로 움직인다.
발행: /map_walls, /patrol_points, /camera_fov, /coverage, /trail,
      TF map->base_footprint, /joint_states
"""
import math, heapq, os
import cv2, numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSDurabilityPolicy, QoSReliabilityPolicy
from geometry_msgs.msg import TransformStamped, Point
from sensor_msgs.msg import JointState, Image
from visualization_msgs.msg import Marker, MarkerArray
from tf2_ros import TransformBroadcaster, StaticTransformBroadcaster

HERE = os.path.dirname(os.path.abspath(__file__))
MAP = os.path.join(HERE, "maps", "map.pgm")
RES, OX, OY = 0.05, -10.0, -10.0

V_LIN, V_ANG, ROBOT_R = 0.22, 0.50, 0.22
CAM_FOV, CAM_RANGE, N_RAYS = math.radians(62), 4.0, 32
SPEED = 3.0          # 재생 배속
DT = 0.1             # 궤적 생성 간격(초)

SPAWN = (3.5, 1.0, 0.0)
PATROL = [(8.10, 1.71), (4.30, -0.55), (1.45, 4.35), (-2.00, -0.80),
          (-7.77, 0.56), (-7.90, -2.95), (7.15, -3.30)]
WHEELS = ["wheel_left_joint", "wheel_right_joint",
          "front_left_wheel", "front_right_wheel", "rear_left_wheel", "rear_right_wheel"]

# 1인칭 카메라 (레이캐스팅으로 합성 — Gazebo 없이 파이프라인 검증용)
IMG_W, IMG_H = 320, 240
CAM_HZ = 5.0
PERSON = (-7.5, 0.30)      # "할머니" — 원래 사각지대였던 좌상단 방에 배치
PERSON_R = 0.30


def read_pgm(path):
    with open(path, "rb") as f:
        d = f.read()
    t, i = [], 0
    while len(t) < 4:
        while d[i:i+1].isspace(): i += 1
        if d[i:i+1] == b"#":
            while d[i:i+1] not in (b"\n", b"\r"): i += 1
            continue
        j = i
        while not d[j:j+1].isspace(): j += 1
        t.append(d[i:j]); i = j
    w, h = int(t[1]), int(t[2]); i += 1
    return np.frombuffer(d[i:i+w*h], np.uint8).reshape(h, w)


img = read_pgm(MAP)
H, W = img.shape
free = (img > 250).astype(np.uint8)
blocked = (img < 250).astype(np.uint8)
distm = cv2.distanceTransform(free, cv2.DIST_L2, 5) * RES
drivable = distm >= ROBOT_R

def to_px(x, y): return int(round((x-OX)/RES)), int(round(H-(y-OY)/RES))
def to_m(px, py): return OX+px*RES, OY+(H-py)*RES


def astar(a, b):
    s, g = to_px(*a), to_px(*b)
    def snap(p):
        if drivable[p[1], p[0]]: return p
        ys, xs = np.nonzero(drivable)
        k = int(np.argmin((xs-p[0])**2 + (ys-p[1])**2))
        return int(xs[k]), int(ys[k])
    s, g = snap(s), snap(g)
    nb = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]
    q = [(0.0, s)]; came = {}; gs = {s: 0.0}
    while q:
        _, c = heapq.heappop(q)
        if c == g: break
        for dx, dy in nb:
            n = (c[0]+dx, c[1]+dy)
            if not (0 <= n[0] < W and 0 <= n[1] < H) or not drivable[n[1], n[0]]: continue
            cost = gs[c] + math.hypot(dx,dy)*(1.0 + 2.0*max(0.0, 0.6-distm[n[1], n[0]]))
            if cost < gs.get(n, 1e18):
                gs[n] = cost; came[n] = c
                heapq.heappush(q, (cost + math.hypot(n[0]-g[0], n[1]-g[1]), n))
    if g not in came and g != s: return None
    p, c = [], g
    while c != s: p.append(to_m(*c)); c = came[c]
    p.append(to_m(*s)); p.reverse()
    return p[::4]


def build_timeline():
    """(x, y, yaw, scan?) 리스트를 DT 간격으로 생성."""
    tl = []
    x, y, yaw = SPAWN
    def emit():
        tl.append((x, y, yaw, False))   # 스캔 여부는 재생 시 인덱스로 판단
    for gx, gy in PATROL:
        path = astar((x, y), (gx, gy))
        if not path: continue
        for wx, wy in path[1:]:
            tgt = math.atan2(wy-y, wx-x)
            d = (tgt - yaw + math.pi) % (2*math.pi) - math.pi
            n = max(1, int(abs(d)/V_ANG/DT))
            for k in range(n):
                yaw += d/n; emit()
            dist = math.hypot(wx-x, wy-y); n = max(1, int(dist/V_LIN/DT))
            x0, y0 = x, y
            for k in range(n):
                f = (k+1)/n; x, y = x0+(wx-x0)*f, y0+(wy-y0)*f; emit()
        n = int(2*math.pi/V_ANG/DT)          # look_around
        y0 = yaw
        for k in range(n):
            yaw = y0 + 2*math.pi*(k+1)/n; emit()
    return tl


def visible_cells(x, y, yaw):
    cx, cy = to_px(x, y); out = []
    for i in range(N_RAYS):
        a = yaw - CAM_FOV/2 + CAM_FOV*i/(N_RAYS-1)
        dx, dy = math.cos(a), -math.sin(a)
        for s in range(1, int(CAM_RANGE/RES)):
            px, py = int(cx+dx*s), int(cy+dy*s)
            if not (0 <= px < W and 0 <= py < H) or blocked[py, px]: break
            out.append((px, py))
    return out


def render_camera(x, y, yaw):
    """맵을 레이캐스팅해서 1인칭 뷰를 합성한다. (frame, 사람보임?, 사람거리)"""
    cx, cy = (x - OX)/RES, H - (y - OY)/RES
    ang = yaw - CAM_FOV/2 + CAM_FOV*np.arange(IMG_W)/(IMG_W-1)
    dx, dy = np.cos(ang), -np.sin(ang)
    dist = np.full(IMG_W, CAM_RANGE*2)
    hit = np.zeros(IMG_W, bool)
    for s in range(2, int(CAM_RANGE*2/RES)):
        px = (cx + dx*s).astype(np.int32); py = (cy + dy*s).astype(np.int32)
        ok = (px >= 0) & (px < W) & (py >= 0) & (py < H) & ~hit
        if not ok.any(): break
        b = np.zeros(IMG_W, bool)
        b[ok] = blocked[py[ok], px[ok]] > 0
        dist[b] = s*RES; hit |= b

    corr = np.maximum(dist * np.cos(ang - yaw), 0.05)          # 어안 보정
    wall_h = np.clip((0.9 / corr) * IMG_H, 4, IMG_H).astype(np.int32)
    top = ((IMG_H - wall_h)//2).astype(np.int32)

    frame = np.zeros((IMG_H, IMG_W, 3), np.uint8)
    frame[:IMG_H//2] = (60, 55, 50)                            # 천장
    frame[IMG_H//2:] = (95, 100, 105)                          # 바닥
    shade = np.clip(255 * (1.0 - corr/(CAM_RANGE*1.3)), 30, 255).astype(np.uint8)
    for c in range(IMG_W):
        if dist[c] >= CAM_RANGE*2: continue
        v = int(shade[c])
        frame[top[c]:top[c]+wall_h[c], c] = (int(v*0.78), int(v*0.84), int(v*0.90))

    # "할머니" 렌더 — FOV 안 + 시야 확보일 때만
    seen, pdist = False, None
    rel = math.atan2(PERSON[1]-y, PERSON[0]-x)
    da = (rel - yaw + math.pi) % (2*math.pi) - math.pi
    pd = math.hypot(PERSON[0]-x, PERSON[1]-y)
    if abs(da) < CAM_FOV/2 and pd < CAM_RANGE:
        n = int(pd/RES)
        clear = True
        for s in range(2, n):
            px = int(cx + math.cos(rel)*s); py = int(cy - math.sin(rel)*s)
            if not (0 <= px < W and 0 <= py < H) or blocked[py, px]: clear = False; break
        if clear:
            seen, pdist = True, pd
            col = int(IMG_W/2 + (da/(CAM_FOV/2))*(IMG_W/2))
            hgt = int(np.clip((0.55/pd)*IMG_H, 8, IMG_H))
            wid = int(np.clip((PERSON_R*2/pd)*IMG_W/(2*math.tan(CAM_FOV/2)), 6, IMG_W))
            t0 = IMG_H//2 - hgt//4
            cv2.rectangle(frame, (col-wid//2, t0), (col+wid//2, t0+hgt), (110, 150, 225), -1)
            cv2.rectangle(frame, (col-wid//2, t0), (col+wid//2, t0+hgt), (60, 90, 160), 1)
    return frame, seen, pdist


class PatrolViz(Node):
    def __init__(self):
        super().__init__("patrol_viz")
        q = QoSProfile(depth=1)
        q.durability = QoSDurabilityPolicy.TRANSIENT_LOCAL
        q.reliability = QoSReliabilityPolicy.RELIABLE

        self.get_logger().info(f"맵 {W}x{H}, 경로 계산 중...")
        self.tl = build_timeline()
        self.get_logger().info(
            f"궤적 {len(self.tl)} 스텝 = {len(self.tl)*DT:.0f}초 (배속 {SPEED}x → {len(self.tl)*DT/SPEED:.0f}초)")

        self.wpub = self.create_publisher(MarkerArray, "/map_walls", q)
        self.ppub = self.create_publisher(MarkerArray, "/patrol_points", q)
        self.fpub = self.create_publisher(Marker, "/camera_fov", 1)
        self.cpub = self.create_publisher(Marker, "/coverage", 1)
        self.tpub = self.create_publisher(Marker, "/trail", 1)
        self.jpub = self.create_publisher(JointState, "/joint_states", 10)
        self.ipub = self.create_publisher(Image, "/camera/image_raw", 1)
        self.cam_every = max(1, int(round((1.0/CAM_HZ)/DT)))
        self.found_at = None
        self.tf = TransformBroadcaster(self)
        self.stf = StaticTransformBroadcaster(self)

        self.wpub.publish(self._walls())
        self.ppub.publish(self._wps())
        self.cover = np.zeros((H, W), np.uint8)
        self.trail = []
        self.i = 0
        self.spin = 0.0
        self.create_timer(DT/SPEED, self.tick)

    def _cube_list(self, mid, ns, pts, rgba, z, scale):
        m = Marker(); m.header.frame_id = "map"; m.ns = ns; m.id = mid
        m.type = Marker.CUBE_LIST; m.action = Marker.ADD
        m.pose.orientation.w = 1.0
        m.scale.x = m.scale.y = scale; m.scale.z = 0.02
        m.color.r, m.color.g, m.color.b, m.color.a = rgba
        for px, py in pts:
            p = Point(); p.x = OX+(px+.5)*RES; p.y = OY+(H-py-.5)*RES; p.z = z
            m.points.append(p)
        return m

    def _walls(self):
        a = MarkerArray()
        ys, xs = np.nonzero(free)
        a.markers.append(self._cube_list(0, "floor", list(zip(xs[::5], ys[::5])),
                                         (.85,.85,.85,.85), 0.0, RES*2.5))
        ys, xs = np.nonzero(img < 100)
        a.markers.append(self._cube_list(1, "wall", list(zip(xs, ys)),
                                         (.12,.12,.12,1.), 0.02, RES))
        return a

    def _wps(self):
        a = MarkerArray()
        for i, (x, y) in enumerate(PATROL):
            m = Marker(); m.header.frame_id="map"; m.ns="wp"; m.id=i
            m.type=Marker.CYLINDER; m.action=Marker.ADD
            m.pose.position.x=x; m.pose.position.y=y; m.pose.position.z=0.03
            m.pose.orientation.w=1.0
            m.scale.x=m.scale.y=0.45; m.scale.z=0.05
            m.color.r, m.color.g, m.color.b, m.color.a = 1.,.2,.2,.9
            a.markers.append(m)
            t = Marker(); t.header.frame_id="map"; t.ns="wplabel"; t.id=100+i
            t.type=Marker.TEXT_VIEW_FACING; t.action=Marker.ADD
            t.pose.position.x=x; t.pose.position.y=y; t.pose.position.z=0.8
            t.pose.orientation.w=1.0; t.scale.z=0.5
            t.color.r,t.color.g,t.color.b,t.color.a = 1.,1.,.2,1.
            t.text=str(i+1); a.markers.append(t)
        # "할머니" 위치 표시
        p = Marker(); p.header.frame_id="map"; p.ns="person"; p.id=900
        p.type=Marker.CYLINDER; p.action=Marker.ADD
        p.pose.position.x, p.pose.position.y, p.pose.position.z = PERSON[0], PERSON[1], 0.3
        p.pose.orientation.w=1.0
        p.scale.x=p.scale.y=PERSON_R*2; p.scale.z=0.6
        p.color.r,p.color.g,p.color.b,p.color.a = .95,.55,.35,.95
        a.markers.append(p)
        pt = Marker(); pt.header.frame_id="map"; pt.ns="person"; pt.id=901
        pt.type=Marker.TEXT_VIEW_FACING; pt.action=Marker.ADD
        pt.pose.position.x, pt.pose.position.y, pt.pose.position.z = PERSON[0], PERSON[1], 1.1
        pt.pose.orientation.w=1.0; pt.scale.z=0.45
        pt.color.r,pt.color.g,pt.color.b,pt.color.a = .95,.6,.4,1.
        pt.text="PERSON"; a.markers.append(pt)
        return a

    def tick(self):
        if self.i >= len(self.tl):
            self.i = 0; self.cover[:] = 0; self.trail.clear()
            self.found_at = None
            self.get_logger().info("한 바퀴 완료 — 다시 시작")
        x, y, yaw, _ = self.tl[self.i]
        now = self.get_clock().now().to_msg()

        t = TransformStamped()
        t.header.stamp = now; t.header.frame_id = "map"; t.child_frame_id = "base_footprint"
        t.transform.translation.x = x; t.transform.translation.y = y
        t.transform.rotation.z = math.sin(yaw/2); t.transform.rotation.w = math.cos(yaw/2)
        self.tf.sendTransform(t)

        self.spin += 0.35
        js = JointState(); js.header.stamp = now
        js.name = WHEELS; js.position = [self.spin]*len(WHEELS)
        self.jpub.publish(js)

        # 카메라 FOV 부채꼴
        f = Marker(); f.header.frame_id="map"; f.header.stamp=now
        f.ns="fov"; f.id=0; f.type=Marker.TRIANGLE_LIST; f.action=Marker.ADD
        f.pose.orientation.w=1.0; f.scale.x=f.scale.y=f.scale.z=1.0
        f.color.r,f.color.g,f.color.b,f.color.a = .2,.6,1.,.25
        prev=None
        for k in range(13):
            a = yaw - CAM_FOV/2 + CAM_FOV*k/12
            p = Point(); p.x=x+CAM_RANGE*math.cos(a); p.y=y+CAM_RANGE*math.sin(a); p.z=0.05
            if prev is not None:
                o=Point(); o.x=x; o.y=y; o.z=0.05
                f.points.extend([o, prev, p])
            prev=p
        self.fpub.publish(f)

        if self.i % self.cam_every == 0:           # 카메라 스트리밍
            frame, seen, pd = render_camera(x, y, yaw)
            if seen and self.found_at is None:
                self.found_at = self.i * DT
                self.get_logger().info(
                    f"*** 사람 발견 ***  t={self.found_at:.0f}s  거리 {pd:.2f}m  "
                    f"로봇 ({x:.2f},{y:.2f})")
            if self.found_at is not None:
                cv2.putText(frame, "PERSON", (8, 22), cv2.FONT_HERSHEY_SIMPLEX,
                            0.6, (90, 230, 90), 2)
            cv2.putText(frame, f"t={self.i*DT:.0f}s", (8, IMG_H-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (220, 220, 220), 1)
            im = Image()
            im.header.stamp = now; im.header.frame_id = "depth_camera_link"
            im.height, im.width = IMG_H, IMG_W
            im.encoding = "bgr8"; im.is_bigendian = 0; im.step = IMG_W*3
            im.data = frame.tobytes()
            self.ipub.publish(im)

        if self.i % 10 == 0:                       # 1Hz 스캔
            for px, py in visible_cells(x, y, yaw):
                self.cover[py, px] = 1
            self.trail.append((x, y))
            ys, xs = np.nonzero(self.cover & free)
            c = self._cube_list(0, "cov", list(zip(xs[::5], ys[::5])),
                                (.35,.9,.35,.75), 0.01, RES*2.5)
            c.header.stamp = now; self.cpub.publish(c)

            tr = Marker(); tr.header.frame_id="map"; tr.header.stamp=now
            tr.ns="trail"; tr.id=0; tr.type=Marker.LINE_STRIP; tr.action=Marker.ADD
            tr.pose.orientation.w=1.0; tr.scale.x=0.05
            tr.color.r,tr.color.g,tr.color.b,tr.color.a = 1.,.5,0.,1.
            for tx, ty in self.trail:
                p=Point(); p.x=tx; p.y=ty; p.z=0.03; tr.points.append(p)
            self.tpub.publish(tr)

            pct = 100*int((self.cover & free).sum())/int(free.sum())
            if self.i % 300 == 0:
                self.get_logger().info(
                    f"t={self.i*DT:5.0f}s  pos=({x:5.2f},{y:5.2f})  커버 {pct:4.1f}%")
        self.i += 1


def main():
    rclpy.init(); n = PatrolViz()
    try: rclpy.spin(n)
    except KeyboardInterrupt: pass
    finally:
        n.destroy_node(); rclpy.try_shutdown()


if __name__ == "__main__":
    main()
