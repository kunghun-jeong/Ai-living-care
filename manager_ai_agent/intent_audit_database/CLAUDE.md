# Intent Audit Database (IAD)

> **구조 정본**: `SOT.md` · **설계 정본**: `docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md`
> **상위**: `manager_ai_agent/` · **Phase**: 1 · **구현 상태**: 미착수

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
