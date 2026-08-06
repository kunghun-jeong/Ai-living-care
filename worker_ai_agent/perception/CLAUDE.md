# Perception Function (PF)

> **구조 정본**: `SOT.md` · **설계 정본**: `docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md`
> **상위**: `worker_ai_agent/` · **Phase**: 0 · **구현 상태**: 구현됨 — **크리티컬 결함 2건**

디바이스 데이터 획득과 상태 모델링. `/camera/image_raw`를 구독해 최신 프레임을 캐시한다.
IF-5(←WAC) · IF-6(→WAA).

**파일**: `Perceptions.py` — `PerceptionModule(node, topic="/camera/image_raw")`
`ReasoningModule`이 기대하는 `FrameSource` 시그니처를 만족한다:
`(frame_id=None) -> {"frame_id","frame","stamp","pose"}`


## 구현 위치 (D-14)

원본 보존 원칙에 따라 실제 코드는 **`worker_ai_agent/limo-MCP/Worker_functions/Perceptions.py`** 에 있다.
이 디렉터리는 **규범(설계·인터페이스·갭)** 을 보유하고, 코드는 두지 않는다.

**구현을 고치기 전에 이 문서의 갭·주의사항을 먼저 읽을 것.**

## ⚠️ G-1 — 프레임 pinning 부재 (크리티컬)

```python
self._latest: Optional[dict] = None          # 슬롯 1개뿐
...
if frame_id is not None and item["frame_id"] != frame_id:
    return None                              # 과거 프레임 조회 불가
```

`PersonScan`이 `f_47`에서 사람을 잡아도, LLM이 `check_object_state(frame_id="f_47")`를 부를 때쯤엔
최신이 `f_53`이라 **증거 이미지를 얻을 수 없다.** 시나리오 1의 결론부가 끊긴다.

**0-7**: N프레임 링버퍼 + `pin(frame_id)`.
단 pin만으로는 부족하다 — `check_object_state`가 pin된 프레임에도 YOLO를 **다시 돌리므로**,
`PersonScan`이 이미 확보한 `hit["bbox"]`를 전달하는 경로도 함께 뚫어야 한다.

## ⚠️ G-2 — `pose`가 항상 `None`

`_on_image`가 `"pose": None`을 하드코딩한다. Report의 `observation.pose`를 채울 수 없다.
**0-8**: TF(`map` ← `base_link`) 조회를 프레임에 스탬프.

## ⚠️ 인코딩 검사 없음 (실물 LIMO 이행 시)

```python
frame = np.frombuffer(msg.data, dtype=np.uint8).reshape(msg.height, msg.width, 3)
```

`msg.encoding`을 보지 않는다. 시뮬 카메라 SDF가 `R8G8B8`(rgb8)인 가정이다.
실물 LIMO는 Orbbec 계열이라 보통 **bgr8**이고, `yolo_detect`의 `frame[:, :, ::-1]`과 겹쳐
**YOLO가 RGB를 보게 되어 정확도가 떨어진다**. depth(16UC1)나 mono8이면 **크래시하거나 쓰레기 배열**이 된다.

## 주의

프레임 rate가 자료마다 다르다 — 스펙 30 Hz / d3d12 시 10 Hz / **실측 ~2·~3.8 Hz**.
**작업 0-0에서 실제 rate를 먼저 측정할 것.** G-1의 위험도가 여기에 좌우된다.
