import { useEffect, useState } from "react";
import { marked } from "marked";
import { api } from "../api.js";

const TABS = ["Filled survey", "Reasoning", "Prompt", "Conversation log"];

const KIND_LABEL = {
  introduction: "Self-introduction",
  raw_completion: "Model completion",
  rejected: "Rejected (guardrail)",
  tool_call: "Tool call",
};

function downloadJson(filename, data) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function downloadJsonl(filename, entries) {
  const blob = new Blob([entries.map((e) => JSON.stringify(e)).join("\n") + "\n"], { type: "application/x-ndjson" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

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

  async function handleDownloadCard() {
    const card = await api.getAgent(surveyId, agentId);
    downloadJson(`${agentId}.card.json`, card);
  }

  function handleDownloadLog() {
    if (trace) downloadJsonl(`${agentId}.conversation.jsonl`, trace.conversation);
  }

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
        <div style={{ padding: "18px 24px", borderBottom: "1px solid var(--border)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h3>{agentId}</h3>
          <div style={{ display: "flex", gap: 8 }}>
            <button className="btn" onClick={handleDownloadCard}>
              Download agent card .json
            </button>
            <button className="btn" onClick={handleDownloadLog} disabled={!trace}>
              Download full log .jsonl
            </button>
            <button className="btn" onClick={onClose}>
              Close
            </button>
          </div>
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
              <div className="mono-dim" style={{ marginBottom: 16, padding: 12, border: "1px solid var(--border)", borderRadius: "var(--radius)" }}>
                This is the complete, timestamped event-by-event trace for this agent, in the exact
                order it happened. The <strong>first</strong> entry is always this agent's own
                self-introduction (it states its ID, model, and role, and confirms its understanding
                of the task, before attempting anything). After that: every model completion
                (<em>Model completion</em>), every attempt guardrails rejected and why
                (<em>Rejected (guardrail)</em>: schema errors, denylist matches, etc., nothing is
                silently dropped), and any tool use (<em>Tool call</em>, e.g. RAG retrieval: what was
                searched and what came back). Use "Download full log .jsonl" above to save the raw
                file.
              </div>
              {trace.conversation.length === 0 && <div className="mono-dim">No events logged yet.</div>}
              {trace.conversation.map((entry, i) => (
                <div key={i} className="panel" style={{ padding: 12, marginBottom: 10 }}>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span className="tag">{KIND_LABEL[entry.kind] || entry.kind}</span>
                    <span className="mono-dim">{entry.logged_at}</span>
                  </div>

                  {entry.kind === "introduction" && (
                    <div style={{ marginTop: 8, whiteSpace: "pre-wrap" }}>{entry.response?.text}</div>
                  )}

                  {entry.kind === "raw_completion" && (
                    <div style={{ marginTop: 8 }}>
                      {entry.response?.raw?.message?.thinking && (
                        <details style={{ marginBottom: 8 }}>
                          <summary className="mono-dim" style={{ cursor: "pointer" }}>
                            Model's internal "thinking" trace (click to expand)
                          </summary>
                          <div style={{ whiteSpace: "pre-wrap", marginTop: 6 }}>{entry.response.raw.message.thinking}</div>
                        </details>
                      )}
                      <div className="mono-dim">Final answer:</div>
                      <pre style={{ whiteSpace: "pre-wrap", fontSize: 12, marginTop: 4 }}>{entry.response?.text || "(empty, see finish_reason)"}</pre>
                      {entry.response?.finish_reason && (
                        <div className="mono-dim">finish_reason: {entry.response.finish_reason}</div>
                      )}
                    </div>
                  )}

                  {entry.kind === "rejected" && (
                    <div style={{ marginTop: 8 }}>
                      <div style={{ color: "var(--red)" }}>{(entry.errors || []).join("; ")}</div>
                      <pre style={{ whiteSpace: "pre-wrap", fontSize: 12, marginTop: 6 }}>{entry.raw_text || "(no text returned)"}</pre>
                    </div>
                  )}

                  {entry.kind === "tool_call" && (
                    <pre style={{ whiteSpace: "pre-wrap", fontSize: 11.5, marginTop: 8, marginBottom: 0 }}>
                      {JSON.stringify(entry, null, 2)}
                    </pre>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
