# Frontend (실험 · 미승인 — 상급자 승인 대기)

> **역할** 자연어를 Manager로 보내고 처리 결과(판단·생성된 intent·Worker 전달 여부)를 화면에서 확인
> **상태** Phase 0 · 로컬 동작 · React(Vite) · **`SOT.md`에 없음, 정본 아님**
> **정본 아님** — 이 디렉터리는 `SOT.md` §2 구조 밖에 있다. 근거는 아래 「주의」참조.

## 주의 — root `CLAUDE.md`·`docs/api-spec.md`와의 충돌

이 저장소의 정본 원칙은 **"HTTP API 없음 — 외부 인터페이스는 MCP tool 6종뿐"** 이다
(root `CLAUDE.md` 8줄, `docs/api-spec.md` 3줄). 이 `frontend/`는 그 원칙을 어기고
`manager_ai_agent/manager_ai_core/api_server.py`(신규, 실험용 HTTP 게이트웨이)에 POST로
자연어를 보낸다.

**팀원 간 합의는 됐으나 상급자 보고·승인 전** (2026-08-18 기준). 그래서:

- `SOT.md` §2 트리·root `CLAUDE.md`·`docs/api-spec.md`는 건드리지 않았다.
- 별도 브랜치에서만 존재하고, 승인 전에는 `main`에 머지하지 않는다.
- 결정 기록: `docs/decisions/2026-08-18-frontend-http-gateway.md`.

## 구성

Vite + React. `npm create vite -- --template react`로 만든 최소 골격 위에 화면 하나만 있다.

| 경로 | 역할 |
|---|---|
| `src/App.jsx` | 입력창 + 전송 → `POST /api/query` → 축별 판단·intent·Worker 전달 여부 표시 |
| `src/` | Vite 표준 구조(`main.jsx`·`App.css`·`index.css` + 정적 이미지 하위 폴더) — 그 외는 스캐폴드 기본값 |
| `public/` | Vite 표준 정적 자산 폴더(favicon 등) — 스캐폴드 기본값, 손대지 않음 |
| `.env` / `.env.example` | `VITE_API_BASE` (Manager API 게이트웨이 주소, 기본 `http://localhost:8000`) |
| `package.json` / `package-lock.json` | npm 의존성 정의 — Vite 스캐폴드 기본값 |
| `.oxlintrc.json` | oxlint 설정 — 스캐폴드 기본값 |

## 실행

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
```

Manager API 게이트웨이(`manager_ai_agent/manager_ai_core/api_server.py`)가 먼저 떠 있어야
한다 — 실행법은 그 파일이 있는 `manager_ai_core/CLAUDE.md` 참조.

## 팀과 정할 것

- 이 원칙 충돌(HTTP API 없음 vs 실제 필요)을 상급자에게 어떻게 보고할지
- 승인되면: `SOT.md` §2에 `frontend/` 등재, 새 인터페이스(IF-9?) 정의, root `CLAUDE.md`·
  `docs/api-spec.md`의 "HTTP API 없음" 문구 개정
- 반려되면: MCP tool 기반(예: Manager가 MCP client, 별도 MCP 서버 노출)으로 재설계
