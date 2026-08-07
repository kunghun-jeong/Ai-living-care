# Intent Audit Database (IAD)

> **역할** 전 계층 의도·정책·결과의 감사 이력 — append-only
> **상태** Phase 1 · 미착수
> **읽을 절** spec **§2.3**(KG↔IAD 구분, 20줄) · **§3.1**(IF-1, 37줄) — 그 외 절은 열지 않는다
> **정본** 구조 `SOT.md` · spec §2.3

intent·policy 이력, 스키마 프롬프트, 검증 규칙을 보관한다. **Intent Validator 기능을 포함**한다.

| | Knowledge Graph | **Intent Audit Database** |
|---|---|---|
| 담는 것 | elder는 보통 living_room에 있다 | 14:03 intent#a1b2 → policy#p7 → LIMO_1 → abnormal |
| 접근 | KG Mapping, 읽기 위주 | 전 계층, **쓰기 위주** + 스키마/프롬프트 읽기 |
| 표준화 | 도메인 데이터 모델 | **감사·보증 데이터 모델 (S-5)** |

## P-5를 실현하는 곳

L0~L4 전 계층 변환과 모든 A2A 메시지가 `intent_id`로 상관되어 기록된다.
**end-to-end 블랙박스 정책 대비 이 프레임워크의 핵심 장점**이므로 논문·제안서의 논거이기도 하다.

## 승계 검토 중인 계약

IETF-125 `k8s_server.py`의 엔드포인트를 계약 그대로 승계하는 안:
`POST /inference` (JSON+base64 이미지 → `logs/json/`, `logs/images/`) · `POST /receive_policy` (YAML)

**ViLaR-IMO 트랙이 지금도 `/inference`를 쓰므로, 유지하면 두 트랙이 같은 감사 저장소를 공유한다.**
판정은 `docs/audit/IETF승계issue.md` §5 (참고 자료, 미채택).
