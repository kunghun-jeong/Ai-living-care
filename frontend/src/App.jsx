import { useState } from "react";
import "./App.css";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

const SEVERITY_LABEL = {
  concern: "우려",
  mild_concern: "경미한 우려",
  info_only: "정보성",
};

function AxisResult({ result }) {
  const { axis, evaluation, sequence } = result;
  return (
    <div className="axis-card">
      <div className="axis-card__header">
        <h3>{axis}</h3>
        <span className={`badge ${evaluation.should_escalate ? "badge--escalate" : "badge--ok"}`}>
          {evaluation.should_escalate ? "에스컬레이션 필요" : "정상"}
        </span>
      </div>

      <div className="axis-card__section">
        <p className="label">발화한 규칙</p>
        {evaluation.triggered_rules.length === 0 ? (
          <p className="muted">없음</p>
        ) : (
          <ul>
            {evaluation.triggered_rules.map((r) => (
              <li key={r.rule_id}>
                <code>{r.rule_id}</code> — {SEVERITY_LABEL[r.severity] || r.severity}
                {r.rationale && <div className="rationale">{r.rationale}</div>}
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="axis-card__section">
        <p className="label">생성된 intent (C3)</p>
        {sequence.intent ? (
          <p className="intent">
            {sequence.intent}
            <span className="muted"> — {sequence.source}</span>
          </p>
        ) : sequence.escalate ? (
          <p className="muted">에스컬레이션 필요하나 대응 로봇 없음</p>
        ) : (
          <p className="muted">특별한 이상 없음 — 로봇 출동 불필요</p>
        )}
      </div>

      <div className="axis-card__section">
        <p className="label">Worker 전달</p>
        <span className={`badge ${result.worker_delivery?.ok ? "badge--ok" : "badge--fail"}`}>
          {result.worker_delivery?.ok ? "Worker 전달됨" : "Worker 전달 실패"}
        </span>
        {result.worker_delivery?.detail && (
          <span className="muted"> — {result.worker_delivery.detail}</span>
        )}
      </div>
    </div>
  );
}

export default function App() {
  const [text, setText] = useState("할머니 괜찮은지 확인해줘");
  const [hour, setHour] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [response, setResponse] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!text.trim()) return;

    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const res = await fetch(`${API_BASE}/api/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text,
          hour: hour === "" ? null : Number(hour),
        }),
      });

      if (!res.ok) {
        const body = await res.text();
        throw new Error(`서버 오류 (${res.status}): ${body}`);
      }

      setResponse(await res.json());
    } catch (err) {
      setError(
        err instanceof TypeError
          ? `Manager API(${API_BASE})에 연결할 수 없습니다. 서버가 떠 있는지 확인하세요.`
          : err.message
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page">
      <header>
        <h1>AI-Care · Manager 콘솔 (실험 · 미승인)</h1>
        <p className="muted">
          자연어 → Manager(Neo4j 추론 파이프라인) → 판단·intent 생성 → Worker 전달
        </p>
      </header>

      <form className="query-form" onSubmit={handleSubmit}>
        <input
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="예: 할머니 괜찮은지 확인해줘"
        />
        <input
          type="number"
          className="hour-input"
          value={hour}
          onChange={(e) => setHour(e.target.value)}
          placeholder="시각(hour), 비우면 현재시각"
          min="0"
          max="23"
        />
        <button type="submit" disabled={loading}>
          {loading ? "처리 중…" : "전송"}
        </button>
      </form>

      {error && <div className="error-box">{error}</div>}

      {response && (
        <div className="results">
          <p className="muted">
            입력: "{response.query}" · 활성 축: {response.active_axes.length > 0 ? response.active_axes.join(", ") : "없음 (OOS)"}
          </p>
          {response.results.length === 0 ? (
            <p className="muted">다룰 수 있는 영역이 아닙니다 (OOS).</p>
          ) : (
            response.results.map((r) => <AxisResult key={r.axis} result={r} />)
          )}
        </div>
      )}
    </div>
  );
}
