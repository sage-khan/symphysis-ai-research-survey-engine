import { useEffect, useState } from "react";
import { marked } from "marked";
import { api } from "../api.js";

const TABS = ["Filled survey", "Reasoning", "Prompt", "Conversation log"];

export default function TraceViewer({ surveyId, agentId, onClose }) {
  const [trace, setTrace] = useState(null);
  const [tab, setTab] = useState(TABS[0]);
  const [error, setError] = useState(null);

  useEffect(() => {
    api
      .getTrace(surveyId, agentId)
      .then(setTrace)
      .catch((err) => setError(String(err.message || err)));
  }, [surveyId, agentId]);

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.6)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 50,
      }}
      onClick={onClose}
    >
      <div
        className="panel"
        style={{ width: "min(900px, 92vw)", maxHeight: "86vh", display: "flex", flexDirection: "column", background: "var(--bg-raised)" }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ padding: "18px 24px", borderBottom: "1px solid var(--border)", display: "flex", justifyContent: "space-between" }}>
          <h3>{agentId}</h3>
          <button className="btn" onClick={onClose}>
            Close
          </button>
        </div>

        <div style={{ display: "flex", gap: 4, padding: "12px 24px 0" }}>
          {TABS.map((t) => (
            <button
              key={t}
              className="btn"
              style={tab === t ? { borderColor: "var(--amber)", color: "var(--amber)" } : {}}
              onClick={() => setTab(t)}
            >
              {t}
            </button>
          ))}
        </div>

        <div style={{ padding: 24, overflowY: "auto", flex: 1 }}>
          {error && <div style={{ color: "var(--red)" }}>{error}</div>}
          {!trace && !error && <div className="mono-dim">Loading...</div>}

          {trace && trace.manual_pending && trace.manual_pending.length > 0 && (
            <div style={{ marginBottom: 16, padding: 12, border: "1px solid var(--amber-dim)", borderRadius: "var(--radius)" }}>
              <span style={{ color: "var(--amber)" }}>⚠ Waiting on a manually-pasted response</span>
              <div className="mono-dim" style={{ marginTop: 4 }}>
                {trace.manual_pending.join(", ")} written under this agent's manual_input/ folder.
              </div>
            </div>
          )}

          {trace && tab === "Filled survey" && (
            <div
              className="markdown-body"
              dangerouslySetInnerHTML={{ __html: marked.parse(trace.filled_survey || "_No filled survey yet._") }}
            />
          )}
          {trace && tab === "Reasoning" && (
            <div
              className="markdown-body"
              dangerouslySetInnerHTML={{ __html: marked.parse(trace.thoughts || "_No reasoning trace yet._") }}
            />
          )}
          {trace && tab === "Prompt" && (
            <pre style={{ whiteSpace: "pre-wrap", fontSize: 12.5 }}>{trace.prompt || "Not sent yet."}</pre>
          )}
          {trace && tab === "Conversation log" && (
            <div>
              {trace.conversation.length === 0 && <div className="mono-dim">No events logged yet.</div>}
              {trace.conversation.map((entry, i) => (
                <div key={i} className="panel" style={{ padding: 12, marginBottom: 10 }}>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span className="tag">{entry.kind}</span>
                    <span className="mono-dim">{entry.logged_at}</span>
                  </div>
                  <pre style={{ whiteSpace: "pre-wrap", fontSize: 11.5, marginTop: 8, marginBottom: 0 }}>
                    {JSON.stringify(entry, null, 2)}
                  </pre>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
