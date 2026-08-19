# Frontend / src

> **역할** Vite React 앱 소스 — 화면 하나(`App.jsx`)만 있다
> **상태** Phase 0 · 실험 · 미승인 — 상위 `../CLAUDE.md` 참조
> **정본 아님** — `SOT.md` §2 구조 밖. 근거는 `../CLAUDE.md`

| 경로 | 역할 |
|---|---|
| `main.jsx` | Vite 진입점 — `App`을 DOM에 마운트 |
| `App.jsx` | 입력창 + 전송 → `POST /api/query` → 축별 판단·intent·Worker 전달 여부 표시 |
| `App.css` / `index.css` | 스타일 — 스캐폴드 기본값 |
| `assets/` | 정적 이미지 — 스캐폴드 기본값 |

나머지는 `npm create vite -- --template react` 골격 그대로다.
