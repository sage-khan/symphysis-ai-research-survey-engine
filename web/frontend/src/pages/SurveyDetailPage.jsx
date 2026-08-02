import { useEffect, useState } from "react";
import { marked } from "marked";
import { api } from "../api.js";
import StatusDot from "../components/StatusDot.jsx";
import AgentForm from "../components/AgentForm.jsx";
import TraceViewer from "../components/TraceViewer.jsx";

function shortDid(did) {
  if (!did) return "";
  return did.length > 28 ? `${did.slice(0, 20)}…${did.slice(-6)}` : did;
}

function WeightTable({ title, bayesian }) {
  if (!bayesian) return null;
  return (
    <div style={{ marginBottom: 24 }}>
      <div className="mono-dim" style={{ marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.04em" }}>
        {title} · {bayesian.num_experts} contributing · {bayesian.method}
      </div>
      <table>
        <thead>
          <tr>
            <th>Criterion</th>
            <th>Mean</th>
            <th>95% CI lower</th>
            <th>95% CI upper</th>
          </tr>
        </thead>
        <tbody>
          {bayesian.criteria.map((c, i) => (
            <tr key={c}>
              <td>{c}</td>
              <td>{bayesian.agg_mean[i].toFixed(4)}</td>
              <td>{bayesian.agg_ci_lower[i].toFixed(4)}</td>
              <td>{bayesian.agg_ci_upper[i].toFixed(4)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function AgentsTab({ surveyId, onChanged }) {
  const [agents, setAgents] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null);
  const [traceAgent, setTraceAgent] = useState(null);

  async function refresh() {
    setAgents(await api.listAgents(surveyId));
    onChanged?.();
  }

  useEffect(() => {
    refresh();
  }, [surveyId]);

  async function handleDelete(agentId) {
    if (!confirm(`Delete agent "${agentId}"?`)) return;
    await api.deleteAgent(surveyId, agentId);
    refresh();
  }

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 16 }}>
        <button
          className="btn btn-primary"
          onClick={() => {
            setEditing(null);
            setShowForm(true);
          }}
        >
          + Add agent
        </button>
      </div>

      {showForm && (
        <AgentForm
          surveyId={surveyId}
          existing={editing}
          onSaved={() => {
            setShowForm(false);
            refresh();
          }}
          onCancel={() => setShowForm(false)}
        />
      )}

      <div className="panel">
        <table>
          <thead>
            <tr>
              <th>Agent</th>
              <th>Role</th>
              <th>Provider / Model</th>
              <th>RAG</th>
              <th>DID</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {agents.map((a) => (
              <tr key={a.agent_id}>
                <td>{a.agent_id}</td>
                <td>{a.role}</td>
                <td>
                  {a.provider}/{a.model}
                </td>
                <td>{a.rag_enabled ? "yes" : "—"}</td>
                <td className="mono-dim" title={a.did}>
                  {shortDid(a.did)}
                </td>
                <td style={{ textAlign: "right", whiteSpace: "nowrap" }}>
                  <button className="btn" onClick={() => setTraceAgent(a.agent_id)} style={{ marginRight: 6 }}>
                    Trace
                  </button>
                  <button
                    className="btn"
                    onClick={async () => {
                      setEditing(await api.getAgent(surveyId, a.agent_id));
                      setShowForm(true);
                    }}
                    style={{ marginRight: 6 }}
                  >
                    Edit
                  </button>
                  <button className="btn btn-danger" onClick={() => handleDelete(a.agent_id)}>
                    Delete
                  </button>
                </td>
              </tr>
            ))}
            {agents.length === 0 && (
              <tr>
                <td colSpan={6} className="mono-dim">
                  No agents yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {traceAgent && <TraceViewer surveyId={surveyId} agentId={traceAgent} onClose={() => setTraceAgent(null)} />}
    </div>
  );
}

function ResultsTab({ surveyId, refreshKey }) {
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api
      .getResults(surveyId)
      .then(setResults)
      .catch((err) => setError(String(err.message || err)));
  }, [surveyId, refreshKey]);

  if (error) return <div className="mono-dim">{error}</div>;
  if (!results) return <div className="mono-dim">Loading...</div>;

  const cr = results.combined_results;

  return (
    <div>
      <WeightTable title="Agent panel" bayesian={cr.agent_panel?.bayesian} />
      <WeightTable title="Human panel" bayesian={cr.human_panel?.bayesian} />
      {cr.hawc_bwm && (
        <div className="mono-dim" style={{ marginBottom: 24 }}>
          HAWC-BWM headline alpha (human weight): <strong style={{ color: "var(--amber)" }}>{cr.hawc_bwm.headline_alpha}</strong>
        </div>
      )}

      {results.charts.length > 0 && (
        <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginBottom: 24 }}>
          {results.charts.map((c) => (
            <img key={c} src={api.chartUrl(surveyId, c)} alt={c} style={{ maxWidth: 460, border: "1px solid var(--border)" }} />
          ))}
        </div>
      )}

      <div className="panel" style={{ padding: 24 }}>
        <div className="markdown-body" dangerouslySetInnerHTML={{ __html: marked.parse(results.report_markdown || "") }} />
      </div>
    </div>
  );
}

export default function SurveyDetailPage({ surveyId, onBack }) {
  const [survey, setSurvey] = useState(null);
  const [tab, setTab] = useState("agents");
  const [status, setStatus] = useState({ status: "idle" });
  const [resultsKey, setResultsKey] = useState(0);

  useEffect(() => {
    api.getSurvey(surveyId).then((s) => {
      setSurvey(s);
      setStatus(s.run_status);
    });
  }, [surveyId]);

  useEffect(() => {
    if (status.status !== "running") return;
    const interval = setInterval(async () => {
      const s = await api.runStatus(surveyId);
      setStatus(s);
      if (s.status !== "running") {
        clearInterval(interval);
        setResultsKey((k) => k + 1);
        if (s.status === "complete") setTab("results");
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [status.status, surveyId]);

  async function handleRun() {
    const s = await api.runSurvey(surveyId);
    setStatus(s);
  }

  if (!survey) return <div className="mono-dim">Loading...</div>;

  return (
    <div>
      <button className="btn" onClick={onBack} style={{ marginBottom: 20 }}>
        ← Surveys
      </button>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20 }}>
        <div>
          <h1>{survey.title}</h1>
          <div className="mono-dim" style={{ marginTop: 6 }}>
            {survey.id} · {survey.instrument} · dimensions: {survey.instrument_params?.dimensions?.join(", ")}
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <StatusDot status={status.status} />
          <a className="btn" href={api.downloadUrl(surveyId)}>
            Download .zip
          </a>
          <button className="btn btn-primary" onClick={handleRun} disabled={status.status === "running"}>
            {status.status === "running" ? "Running…" : "Run survey"}
          </button>
        </div>
      </div>

      {status.status === "error" && (
        <div className="panel" style={{ padding: 16, marginBottom: 20, borderColor: "var(--red)" }}>
          <pre style={{ whiteSpace: "pre-wrap", fontSize: 12, color: "var(--red)", margin: 0 }}>{status.message}</pre>
        </div>
      )}

      {status.status === "pending_manual" && (
        <div className="panel" style={{ padding: 16, marginBottom: 20, borderColor: "var(--amber-dim)" }}>
          <div style={{ color: "var(--amber)", marginBottom: 4 }}>⚠ Waiting on manually-pasted responses</div>
          <div className="mono-dim">{status.message} Check each manual agent's Trace tab for its exact prompt to paste.</div>
        </div>
      )}

      <div style={{ display: "flex", gap: 8, marginBottom: 20 }}>
        {["agents", "results"].map((t) => (
          <button
            key={t}
            className="btn"
            style={tab === t ? { borderColor: "var(--amber)", color: "var(--amber)" } : {}}
            onClick={() => setTab(t)}
          >
            {t === "agents" ? "Agents" : "Results"}
          </button>
        ))}
      </div>

      {tab === "agents" && <AgentsTab surveyId={surveyId} />}
      {tab === "results" && <ResultsTab surveyId={surveyId} refreshKey={resultsKey} />}
    </div>
  );
}
