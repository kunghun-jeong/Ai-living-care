# IETF-125 / IETF-126 승계 이슈 — 참고 자료

> **문서 성격**: 참고용(reference only). 결정 사항이 아니며 통합 아키텍처 스펙에 반영되지 않았다.
> 필요할 때 꺼내 보고, 채택하기로 하면 그때 스펙에 옮긴다.
>
> **대상**: `github.com/jaehoonpauljeong/I2ICF` — `IETF-126/`, `IETF-125/`
> **작성일**: 2026-08-06 · **근거**: 저장소 clone 후 전 소스 직접 확인

---

## 0. 한 줄 판정

**직접 구현.** 두 저장소 합계 약 1,500줄 중 실제로 가져올 Python은 **130줄 내외(10% 미만)**이고, 나머지는 계층이 달라 이식 자체가 불가능하다. 다만 **인터페이스 계약 3개는 의도적으로 승계**할 가치가 있다.

---

## 1. 저장소 실태

### IETF-126

- 커밋 **2개**, 둘 다 2026-07-14. Vienna 해커톤(7/18~24) **나흘 전** 일괄 업로드 후 미수정.
- 파이프라인: React → Django `POST /api/infer/` → Ollama Llama 3.1 8B(few-shot) → `{mode, command, speed, duration, target_class}` → 3분기
  - `action` — 19개 dict 조회 → `(linear_x, angular_z)` → 10 Hz로 `duration`초 Twist 발행
  - `trace` — YOLO bbox를 화면 중앙 정렬 + bbox 높이 비율로 접근/후퇴
  - `detection` — 사람 감지 시 좌·우·좌 흔들기("인사")

### IETF-125

- Robot–Edge–Cloud 3자 구조. `edge_control.py`(17 KB)가 폴링 스레드 5개로 카메라·odom·LiDAR를 각각 HTTP로 받아 YOLO + camera–LiDAR 융합 수행.
- 회피는 하드코딩 S-curve 4단계: `우 n° k초 → 좌 n° 2k초 → 우 n° k초 → 정렬 후 전진`.

---

## 2. 왜 대량 이식이 불가능한가 — 계층 불일치

| | IETF-125/126 | limo-MCP (현행) |
|---|---|---|
| 목표 표현 | "0.2 m/s로 2초" / "우측 0.35 rad/s" | map 프레임 `(x, y, yaw)` |
| 상태 관리 | 전역 dict (`drive_state`, `avoid_state`) | Nav2 goal handle + task 상태 |
| 구조 | 폴링 스레드 5개 + 단계마다 HTTP | 단일 ROS2 노드 + 생성자 주입 |
| 회피/재계획 | 하드코딩 S-curve | Nav2 global planner |
| 지도·측위 | **없음** | slam_toolbox (+ 향후 AMCL) |

**IETF-126은 "거실로 가"를 실행할 수 없다.** 목표 좌표라는 개념 자체가 없고 "앞으로 N초"만 있다. `robot_map.pgm`이 저장소에 있으나 **읽는 코드가 없고**, `/astar_waypoints`를 rosbridge에서 advertise하지만 **publish하는 코드가 어디에도 없다.**

### 역방향 오염 위험

limo-MCP의 `Reasonings.py`(ROS2 비의존 순수 로직 + 백엔드 주입)는 I2ICF 전체를 통틀어 가장 깨끗한 설계다. `edge_control.py`의 전역 캐시 + 스레드 구조를 끌어오면 이 자산이 손상된다. ViLaR-IMO 문서 스스로 같은 문제를 기록하고 있다 — *"hard-coded host, model path, threshold를 환경변수 또는 config file로 분리할 필요"*, *"`imo_control.py`와 waypoint follower가 동시에 `/cmd_vel`을 publish하면 command arbitration이 없어 충돌"*.

---

## 3. 컴포넌트별 판정

| 남은 작업 | 판정 | 근거 |
|---|---|---|
| MAC: intent → L1 → L2 | **직접** (프롬프트 *형태*만 참고) | IETF-126 프롬프트는 이동 동사 19개 전용 |
| **LLM 실패 대비 fallback** | **뽑아쓰기 (~60줄)** | §4.1 |
| KG / 장소 룩업 (G-6) | **직접** | 양쪽 모두 없음 |
| A2A / `execute_policy` 계층 | **직접** | I2ICF 전체에 유사물 없음 |
| Policy Translator (L2→L3) | **직접** (`ACTION_TABLE`을 선례로 인용) | §4.3 |
| G-1~G-5 (pinning·pose·tool 노출·look_around·콜백 가드) | **전부 직접** | 프레임 버퍼·TF·MCP·Nav2 goal handle 모두 I2ICF에 없음 |
| IAD 감사 로그 | **계약 승계 + 직접 구현** | §5 |
| 안전 정지 | **게이트 패턴만 (~20줄)** | §4.2 — 트리거 로직은 폐기 |
| Camera–LiDAR 융합 (Phase 1+) | **쓰지 말 것** | §6 |
| YANG 데이터 모델 (S-1/S-2) | **통째로 가져오기** | §5-3 |
| 데모 UI | **가져다 쓰기** | 연구 가치 0, 데모 가치 실재 |

---

## 4. 뽑아쓸 것

### 4.1 `_fallback()` + `_normalize()` — IETF-126 `backend/intentString/services/limo_llm.py`

LLM 호출이 타임아웃·파싱 실패하면 키워드 매칭으로 내려앉고, `_normalize()`가 필드별 기본값을 채운다.

**가치**: 스펙의 **P-4(실패 안전)** 가 "LLM이 스키마에 안 맞는 출력을 뱉으면 어떻게 되는가"에 아직 답이 없다. 여기에 동작하는 답이 있다. MAC의 L1→L2 생성 단계에 같은 3단 구조(정상 파싱 → 필드 정규화 → 규칙 기반 폴백)를 두면 된다.

**부수 팁**: Ollama 호출에 `format: "json"`을 걸어 출력 형식을 강제한다.

### 4.2 e-stop 게이트 **위치** — IETF-126 `services/rosbridge.py`

```python
def publish_cmd_vel(self, linear_x, angular_z):
    if self._estop:
        self.stop_robot(); return
    ...
```

안전 검사가 **명령 경로 안쪽**에 있어 어떤 경로로 명령을 쏘든 우회가 불가능하다. slide 18의 "Action Function이 Session Key Check를 한 번 더 수행한다"는 이중 검증 구조와 같은 발상이다.

> **⚠️ 트리거는 반드시 폐기할 것.** 현재 조건은 `bbox 높이 / 프레임 높이 ≥ 0.65`인데:
> - **바닥에 누운 사람은 짧고 넓은 bbox**라 걸리지 않는다.
> - 쓰러진 사람은 멈출 대상이 아니라 **다가갈 대상**이다.
> - 카메라 스냅샷 실패 시 `frame is None → continue`로 넘어가 e-stop을 걸지 않는다. **로봇이 눈먼 채로 계속 주행한다.**
>
> 리빙케어에서는 정확히 반대로 작동한다. 게이트 위치만 취하고 판정은 새로 설계할 것.

### 4.3 `ACTION_TABLE` — IETF-126 `services/function_table.py`

동사 → `(linear_x, angular_z)` 19개 매핑. 조직 코드 전체에서 "고수준 명령 → 저수준 작동 파라미터"를 명시적 테이블로 만든 **유일한 사례**다. 코드를 쓰는 게 아니라 **L3 저수준 정책의 실물 선례로 논문·제안서에 인용**할 값어치가 있다.

---

## 5. 승계할 인터페이스 계약 3개 — 실익의 핵심

코드가 아니라 **계약**을 승계하는 것이 제안서·논문에서 값어치가 있다. Flask 로거 50줄 복사는 계보가 아니지만, 인터페이스 유지는 계보다.

1. **`POST /inference`** (JSON + base64 이미지 → `logs/json/`, `logs/images/`) — IETF-125 `k8s_server.py`
   코드는 15분이면 새로 짜지만, **ViLaR-IMO 트랙이 지금도 이 엔드포인트를 쓴다.** 계약을 유지하면 두 트랙이 같은 감사 저장소를 공유하고 **IAD의 실체가 공짜로 생긴다.**

2. **`POST /receive_policy`** (YAML 정책 수신) — IETF-125 `intent_server.py`
   L2 정책 수신 종단점의 조직 표준형.

3. **I2NSF YANG 계보** — `IETF-126/frontend/IETF-I~1.YAN`
   `ietf-i2nsf-cons-facing-interface`, **1,773줄**, revision 2022-05-23. **표준화 목표 기준 이 저장소에서 가장 값진 파일**이며 S-1(High-level Policy Data Model)의 직접 템플릿이다.
   현재 상태: **프론트엔드 폴더에 Windows 8.3 방식으로 이름이 깨진 채 아무 코드도 참조하지 않고 방치**되어 있다.

---

## 6. 쓰지 말아야 할 것 — IETF-125 camera–LiDAR 융합

`edge_control.py`의 융합은 초안 수준이고 **ViLaR-IMO가 이미 앞서 있다.**

```python
ratio     = cx / image_w
angle_rel = (ratio - 0.5) * fov_rad      # 픽셀 → 각도 선형 매핑
idx       = int((angle_global - angle_min) / angle_inc)
dist      = ranges[idx]                   # 단일 광선 1개
```

**결함 3건**

1. **선형 픽셀→각도 매핑이 rectilinear 카메라에서 틀리다.** 올바른 식은 `θ = atan(u·tan(FOV/2))`. FOV 71°, 화면 중간(u=0.5)에서 실제 **19.6°** vs 계산 **17.8°** — 약 **1.9° 오차**. `LIDAR_LEN=401` 기준 인덱스 2~4칸에 해당하고, **광선을 하나만 뽑기 때문에** 그만큼 어긋나면 사람 대신 뒤 배경 거리를 집는다.
2. **extrinsic 무시** — `angle_global = angle_rel`. LIMO 라이다는 base_link 기준 `(0.103, 0, −0.034)`에 있다.
3. **시간 동기화 없음** — 카메라와 LiDAR가 독립 스레드의 별개 캐시.

ViLaR-IMO는 **bbox x범위 전체의 후보를 모아 가까운 값들의 median**을 쓴다. 구조적으로 우월하다. 융합이 필요해지면 **ViLaR 쪽에서 가져올 것.**

---

## 7. 저장소 자체의 결함 (인용·재사용 시 주의)

### 7.1 "Intent Translator"가 죽은 코드

`draft-gu-nmrg-intent-translator`와 이름을 공유하는 `IETF-126/backend/intranslator/` 앱은:

- `upload_file()`이 **문자열 리터럴** `'VIRTUALSERVER_IPADDRESS/UPLOAD'`로 POST한다 — 실제 URL이 아니다.
- `intranslator/urls.py`가 `upload_file`/`get_intents`/`home`을 **라우팅하지 않는다** (admin + intentString 4개만).
- **`INSTALLED_APPS`에 등록조차 되어 있지 않다.** 따라서 models·migrations도 전부 고아다.
- 파일의 절반이 주석 처리되어 있고, `mapping_rules.yaml`의 샘플 정책 값은 `"hello"/"hello"/"hello"`.

### 7.2 "정책"의 실체

I2ICF 저장소 전체에서 정책이 실제로 동작을 좌우하는 **유일한 지점**은 IETF-125의 이 함수다.

```python
action = data["i2nsf-security-policy"]["rules"]["action"]["packet-action"]["ingress-action"]
return action == "pass"
```

방화벽 스키마에서 빌려온 **boolean pass/drop 하나**로 distance 전송을 켜고 끈다. 그 `received_policy.yaml`은 `192.168.18.200`의 TCP:80을 drop하는 **진짜 방화벽 규칙**이며 로보틱스용 각색이 전혀 없다.

> 팀 문서가 *"I2ICF-compliant full implementation"이 아니라 "I2ICF-based / I2ICF-aligned prototype"으로 표현하는 것이 안전하다"* 고 경고한 근거가 바로 이것이다. 제안서에서 이 저장소를 구현 실적으로 인용할 때 심사자가 열어보면 보이는 부분이다.

### 7.3 위생 문제

| 항목 | 상태 |
|---|---|
| `requirements.txt` | **없음** (Django·DRF·requests·websocket-client·ultralytics·opencv·numpy·PyYAML 전부 버전 미상) |
| `SECRET_KEY` | `django-insecure-93tg4neb@s*5dz5a7#3dk*3aygku2d7&q9fq4!b6ll&0al4pct` **커밋됨** |
| `DEBUG` | `True`, `ALLOWED_HOSTS = []` |
| LIMO IP | `192.168.50.165` **하드코딩** (해커톤 LAN) |

---

## 8. 제안서·논문에 쓸 때의 서술 방침

**뽑아쓸 게 적은 것은 코드가 나빠서가 아니라, 아직 아무도 그 층을 만들지 않았기 때문이다.** L0→L4 정책 연속체는 조직 안에 선례가 없다. 이것이 곧 표준화 제안의 novelty 논거다.

- ❌ "기존 구현을 재사용한다"
- ✅ **"검증된 인터페이스를 승계하고, 그 위에 없던 정책 계층을 표준화한다"**

실적으로서의 값어치는 **시연했다는 사실 자체**(IETF-126 Vienna, 오픈소스 공개, 데모 영상)에 있고 **코드 품질은 논거가 아니다.** 다만 심사자가 저장소를 열어볼 가능성을 감안하면 `requirements.txt` 추가와 죽은 `intranslator` 정리는 최소 위생 조치로 해둘 만하다.

---

## 참고 자료

- [I2ICF 저장소](https://github.com/jaehoonpauljeong/I2ICF) — `IETF-126/`, `IETF-125/` (그 외 IETF-120~124, Side-Meeting 별도)
- [IETF-126 데모 영상](https://www.youtube.com/watch?v=ZKX4iXNa774)
- IETF-125 데모 영상: `https://youtu.be/589GNGIX3fk`
- 관련 I-D: [intent-translator](https://datatracker.ietf.org/doc/draft-gu-nmrg-intent-translator/03/) · [ibn-network-management-automation](https://datatracker.ietf.org/doc/draft-jeong-nmrg-ibn-network-management-automation/07/) · [5g-security-i2nsf-framework](https://datatracker.ietf.org/doc/draft-ahn-nmrg-5g-security-i2nsf-framework/02/)
- 통합 아키텍처 스펙: `AI-Care_Unified_Architecture_Spec_v0.2.md`
