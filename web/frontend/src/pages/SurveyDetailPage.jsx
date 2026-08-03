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

const STATUS_LABEL = {
  contributed: "Contributed",
  zero_accepted: "Zero accepted",
  pending_manual: "Pending manual",
  skipped: "Skipped",
  not_run: "Not run",
};

const STATUS_COLOR = {
  contributed: "var(--green, #3fb950)",
  zero_accepted: "var(--red, #e5534b)",
  pending_manual: "var(--amber)",
  skipped: "var(--red, #e5534b)",
  not_run: "var(--muted, #888)",
};

function AnalyticsTab({ surveyId, refreshKey }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api
      .getAnalytics(surveyId)
      .then(setData)
      .catch((err) => setError(String(err.message || err)));
  }, [surveyId, refreshKey]);

  if (error) return <div className="mono-dim">{error}</div>;
  if (!data) return <div className="mono-dim">Loading...</div>;

  const contributing = data.per_agent.filter((a) => a.status === "contributed");
  const nonContributing = data.per_agent.filter((a) => a.status !== "contributed");
  const totalSamples = contributing.reduce((n, a) => n + a.samples.length, 0);

  return (
    <div>
      <div className="mono-dim" style={{ marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.04em" }}>
        Panel participation
      </div>
      <div className="panel" style={{ padding: "12px 16px", marginBottom: 24, display: "flex", gap: 28, flexWrap: "wrap" }}>
        {Object.entries(data.summary).map(([status, count]) => (
          <div key={status}>
            <div style={{ fontSize: 22, color: STATUS_COLOR[status] }}>{count}</div>
            <div className="mono-dim" style={{ fontSize: 12 }}>
              {STATUS_LABEL[status]}
            </div>
          </div>
        ))}
      </div>

      <div className="mono-dim" style={{ marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.04em" }}>
        Best / worst pick frequency ({totalSamples} accepted samples across {contributing.length} agents)
      </div>
      <div className="panel" style={{ marginBottom: 24 }}>
        <table>
          <thead>
            <tr>
              <th>Criterion</th>
              <th>Picked Best</th>
              <th>Picked Worst</th>
            </tr>
          </thead>
          <tbody>
            {data.best_worst_frequency.map((row) => (
              <tr key={row.criterion}>
                <td>{row.criterion}</td>
                <td>{row.best_count}</td>
                <td>{row.worst_count}</td>
              </tr>
            ))}
            {data.best_worst_frequency.length === 0 && (
              <tr>
                <td colSpan={3} className="mono-dim">
                  No accepted samples yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="mono-dim" style={{ marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.04em" }}>
        Weight elicitation details — who said what
      </div>
      <div className="panel" style={{ marginBottom: 24 }}>
        <table>
          <thead>
            <tr>
              <th>Agent</th>
              <th>Role</th>
              <th>Model</th>
              <th>RAG</th>
              <th>#</th>
              <th>Best</th>
              <th>Worst</th>
              <th>Reasoning</th>
            </tr>
          </thead>
          <tbody>
            {contributing.flatMap((a) =>
              a.samples.map((s) => (
                <tr key={`${a.agent_id}-${s.index}`}>
                  <td>{a.agent_id}</td>
                  <td>{a.role}</td>
                  <td>
                    {a.provider}/{a.model}
                  </td>
                  <td>{a.rag_enabled ? "yes" : "—"}</td>
                  <td>{s.index}</td>
                  <td style={{ color: "var(--amber)" }}>{s.best}</td>
                  <td>{s.worst}</td>
                  <td title={s.reasoning} style={{ maxWidth: 420, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {s.reasoning}
                  </td>
                </tr>
              )),
            )}
            {contributing.length === 0 && (
              <tr>
                <td colSpan={8} className="mono-dim">
                  No agent has contributed an accepted sample yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="mono-dim" style={{ marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.04em" }}>
        Non-contributing agents
      </div>
      <div className="panel">
        <table>
          <thead>
            <tr>
              <th>Agent</th>
              <th>Role</th>
              <th>Model</th>
              <th>Status</th>
              <th>Why</th>
            </tr>
          </thead>
          <tbody>
            {nonContributing.map((a) => (
              <tr key={a.agent_id}>
                <td>{a.agent_id}</td>
                <td>{a.role}</td>
                <td>
                  {a.provider}/{a.model}
                </td>
                <td style={{ color: STATUS_COLOR[a.status] }}>{STATUS_LABEL[a.status]}</td>
                <td className="mono-dim">{a.detail}</td>
              </tr>
            ))}
            {nonContributing.length === 0 && (
              <tr>
                <td colSpan={5} className="mono-dim">
                  Every configured agent contributed at least one accepted sample.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function AddFromLibrary({ surveyId, onAdded, onCancel }) {
  const [libraryAgents, setLibraryAgents] = useState([]);
  const [selected, setSelected] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.listLibraryAgents().then(setLibraryAgents);
  }, []);

  async function handleAssign() {
    if (!selected) return;
    setBusy(true);
    setError(null);
    try {
      await api.assignLibraryAgentToSurvey(selected, surveyId);
      onAdded();
    } catch (err) {
      setError(String(err.message || err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="panel" style={{ padding: 24, marginBottom: 24, display: "flex", gap: 12, alignItems: "flex-end" }}>
      <label style={{ flex: 1 }}>
        <div className="mono-dim">Library agent</div>
        <select value={selected} onChange={(e) => setSelected(e.target.value)} style={{ width: "100%" }}>
          <option value="">select an agent from the library...</option>
          {libraryAgents.map((a) => (
            <option key={a.agent_id} value={a.agent_id}>
              {a.agent_id} -- {a.display_name || a.role} ({a.provider}/{a.model})
            </option>
          ))}
        </select>
        {libraryAgents.length === 0 && (
          <div className="mono-dim" style={{ marginTop: 4 }}>
            No library agents yet -- create one on the Agent Library page first.
          </div>
        )}
      </label>
      <button className="btn btn-primary" onClick={handleAssign} disabled={busy || !selected}>
        Add to survey
      </button>
      <button className="btn" onClick={onCancel}>
        Cancel
      </button>
      {error && <div style={{ color: "var(--red)" }}>{error}</div>}
    </div>
  );
}

function AgentsTab({ surveyId, onChanged }) {
  const [agents, setAgents] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [showLibraryPicker, setShowLibraryPicker] = useState(false);
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
      <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, marginBottom: 16 }}>
        <button className="btn" onClick={() => setShowLibraryPicker((v) => !v)}>
          {showLibraryPicker ? "Cancel" : "+ Add from library"}
        </button>
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

      {showLibraryPicker && (
        <AddFromLibrary
          surveyId={surveyId}
          onAdded={() => {
            setShowLibraryPicker(false);
            refresh();
          }}
          onCancel={() => setShowLibraryPicker(false)}
        />
      )}

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
              <th>Display name</th>
              <th>Role / expertise</th>
              <th>Provider / Model</th>
              <th>RAG</th>
              <th>Tools</th>
              <th>DID</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {agents.map((a) => (
              <tr key={a.agent_id}>
                <td>{a.agent_id}</td>
                <td>{a.display_name || <span className="mono-dim">—</span>}</td>
                <td>
                  {a.role}
                  {a.expertise && <div className="mono-dim">{a.expertise}</div>}
                </td>
                <td>
                  {a.provider}/{a.model}
                </td>
                <td>{a.rag_enabled ? "yes" : "—"}</td>
                <td>{a.tools && a.tools.length ? a.tools.join(", ") : "—"}</td>
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
                <td colSpan={8} className="mono-dim">
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

  async function handleRename() {
    const next = prompt("Rename project", survey.title);
    if (!next || !next.trim() || next.trim() === survey.title) return;
    const updated = await api.renameSurvey(surveyId, next.trim());
    setSurvey(updated);
  }

  if (!survey) return <div className="mono-dim">Loading...</div>;

  return (
    <div>
      <button className="btn" onClick={onBack} style={{ marginBottom: 20 }}>
        ← Surveys
      </button>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20 }}>
        <div>
          <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
            <h1>{survey.title}</h1>
            <button className="btn" onClick={handleRename} style={{ fontSize: 12 }}>
              Rename
            </button>
          </div>
          {survey.description && <div style={{ marginTop: 4, maxWidth: 640 }}>{survey.description}</div>}
          <div className="mono-dim" style={{ marginTop: 6 }}>
            {survey.id} · {survey.instrument} · dimensions: {survey.instrument_params?.dimensions?.join(", ")}
            {survey.created_at && <> · created {survey.created_at.slice(0, 16).replace("T", " ")} UTC</>}
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
        {["agents", "results", "analytics"].map((t) => (
          <button
            key={t}
            className="btn"
            style={tab === t ? { borderColor: "var(--amber)", color: "var(--amber)" } : {}}
            onClick={() => setTab(t)}
          >
            {{ agents: "Agents", results: "Results", analytics: "Analytics" }[t]}
          </button>
        ))}
      </div>

      {tab === "agents" && <AgentsTab surveyId={surveyId} />}
      {tab === "results" && <ResultsTab surveyId={surveyId} refreshKey={resultsKey} />}
      {tab === "analytics" && <AnalyticsTab surveyId={surveyId} refreshKey={resultsKey} />}
    </div>
  );
}
