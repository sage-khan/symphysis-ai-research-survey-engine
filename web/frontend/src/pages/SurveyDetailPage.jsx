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

function formatBytes(n) {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

function KnowledgeTab({ surveyId }) {
  const [files, setFiles] = useState([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  async function refresh() {
    setFiles(await api.listKnowledgeFiles(surveyId));
  }

  useEffect(() => {
    refresh();
  }, [surveyId]);

  async function handleUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      await api.uploadKnowledgeFile(surveyId, file);
      await refresh();
    } catch (err) {
      setError(String(err.message || err));
    } finally {
      setBusy(false);
      e.target.value = "";
    }
  }

  async function handleDelete(filename) {
    if (!confirm(`Delete "${filename}" from the shared knowledge repository?`)) return;
    await api.deleteKnowledgeFile(surveyId, filename);
    refresh();
  }

  return (
    <div>
      <div className="mono-dim" style={{ marginBottom: 16, maxWidth: 720 }}>
        Files uploaded here are shared, survey-wide background material -- every agent in this
        survey retrieves relevant chunks from it automatically when the survey runs, with no
        per-agent setup needed (distinct from a single role's own dedicated RAG corpus, configured
        on that agent). .md/.txt are stored as-is; .pdf/.docx are converted to plain text on upload
        (best-effort extraction, review the result if formatting mattered).
      </div>

      <div style={{ marginBottom: 20 }}>
        <input type="file" accept=".md,.markdown,.txt,.pdf,.docx" onChange={handleUpload} disabled={busy} />
        {error && <div style={{ color: "var(--red)", marginTop: 8 }}>{error}</div>}
      </div>

      <div className="panel">
        <table>
          <thead>
            <tr>
              <th>File</th>
              <th>Size</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {files.map((f) => (
              <tr key={f.filename}>
                <td>{f.filename}</td>
                <td className="mono-dim">{formatBytes(f.size_bytes)}</td>
                <td style={{ textAlign: "right" }}>
                  <button className="btn btn-danger" onClick={() => handleDelete(f.filename)}>
                    Delete
                  </button>
                </td>
              </tr>
            ))}
            {files.length === 0 && (
              <tr>
                <td colSpan={3} className="mono-dim">
                  No shared knowledge files yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

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

function AgentProposer({ surveyId, onApproved, onCancel }) {
  const [requirement, setRequirement] = useState("");
  const [providers, setProviders] = useState([]);
  const [provider, setProvider] = useState("ollama");
  const [modelCatalog, setModelCatalog] = useState({ models: [], error: null });
  const [model, setModel] = useState("");
  const [proposals, setProposals] = useState(null);
  const [results, setResults] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.listProviders().then(setProviders);
  }, []);

  useEffect(() => {
    api.listModelsForProvider(provider).then((r) => {
      setModelCatalog(r);
      if (r.models?.length) setModel(r.models[0]);
    });
  }, [provider]);

  async function handlePropose() {
    setBusy(true);
    setError(null);
    setResults(null);
    try {
      const proposed = await api.proposeAgents(surveyId, { requirement, provider, model });
      setProposals(proposed);
    } catch (err) {
      setError(String(err.message || err));
    } finally {
      setBusy(false);
    }
  }

  function updateProposal(i, field, value) {
    setProposals((prev) => prev.map((p, idx) => (idx === i ? { ...p, [field]: value } : p)));
  }

  function removeProposal(i) {
    setProposals((prev) => prev.filter((_, idx) => idx !== i));
  }

  async function handleApprove() {
    setBusy(true);
    setError(null);
    try {
      const outcome = await api.approveAgents(surveyId, proposals);
      setResults(outcome);
      if (outcome.every((r) => r.status !== "error")) {
        setTimeout(onApproved, 800);
      }
    } catch (err) {
      setError(String(err.message || err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="panel" style={{ padding: 24, marginBottom: 24 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <h3>Describe the panel you need</h3>
        <button className="btn" onClick={onCancel}>
          Close
        </button>
      </div>
      <div className="mono-dim" style={{ marginBottom: 16 }}>
        Write your requirement in plain language. An LLM (picked below) proposes agents -- reusing
        Agent Library entries where they fit, or drafting new ones -- as an editable list. Nothing
        is created until you review and click Approve.
      </div>

      <label style={{ display: "block", marginBottom: 16 }}>
        <div className="mono-dim">Requirement</div>
        <textarea
          value={requirement}
          onChange={(e) => setRequirement(e.target.value)}
          rows={3}
          placeholder="e.g. I need a panel covering structural engineering, blockchain/DLT, and GDPR compliance for a construction data-trust survey."
          style={{ width: "100%" }}
        />
      </label>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr auto", gap: 12, marginBottom: 16, alignItems: "end" }}>
        <label>
          <div className="mono-dim">Orchestrator provider</div>
          <select value={provider} onChange={(e) => setProvider(e.target.value)} style={{ width: "100%" }}>
            {providers.filter((p) => p !== "manual").map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </label>
        <label>
          <div className="mono-dim">Model</div>
          {modelCatalog.models.length > 0 ? (
            <select value={model} onChange={(e) => setModel(e.target.value)} style={{ width: "100%" }}>
              {modelCatalog.models.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          ) : (
            <input value={model} onChange={(e) => setModel(e.target.value)} style={{ width: "100%" }} />
          )}
          {modelCatalog.error && (
            <div className="mono-dim" style={{ color: "var(--amber)", marginTop: 4 }}>
              ⚠ {modelCatalog.error}
            </div>
          )}
        </label>
        <button className="btn btn-primary" onClick={handlePropose} disabled={busy || !requirement.trim() || !model}>
          {busy ? "Thinking…" : "Propose agents"}
        </button>
      </div>

      {error && <div style={{ color: "var(--red)", marginBottom: 16 }}>{error}</div>}

      {proposals && (
        <div>
          <div className="mono-dim" style={{ marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.04em" }}>
            Proposed agents -- review and edit before approving
          </div>
          <table style={{ marginBottom: 16 }}>
            <thead>
              <tr>
                <th>Source</th>
                <th>Agent ID</th>
                <th>Display name</th>
                <th>Role</th>
                <th>Model</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {proposals.map((p, i) => (
                <tr key={i}>
                  <td>{p.source === "library" ? "library (reuse)" : "new"}</td>
                  <td className="mono-dim">{p.agent_id}</td>
                  <td>
                    {p.source === "new" ? (
                      <input
                        value={p.display_name || ""}
                        onChange={(e) => updateProposal(i, "display_name", e.target.value)}
                        style={{ width: "100%" }}
                      />
                    ) : (
                      "—"
                    )}
                  </td>
                  <td>
                    {p.source === "new" ? (
                      <input value={p.role || ""} onChange={(e) => updateProposal(i, "role", e.target.value)} style={{ width: "100%" }} />
                    ) : (
                      "—"
                    )}
                  </td>
                  <td>
                    {p.source === "new" ? (
                      <div>
                        <input
                          value={p.model?.name || ""}
                          onChange={(e) => updateProposal(i, "model", { ...p.model, name: e.target.value })}
                          style={{ width: "100%" }}
                        />
                        {p.model_available === false && (
                          <div style={{ color: "var(--amber)", fontSize: 12 }}>
                            ⚠ not found on this Ollama host -- pick a real model or pull this one first
                          </div>
                        )}
                      </div>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td>
                    <button className="btn btn-danger" onClick={() => removeProposal(i)}>
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <button className="btn btn-primary" onClick={handleApprove} disabled={busy || proposals.length === 0}>
            Approve & add to survey
          </button>
        </div>
      )}

      {results && (
        <div style={{ marginTop: 16 }}>
          {results.map((r, i) => (
            <div key={i} className="mono-dim" style={{ color: r.status === "error" ? "var(--red)" : "var(--green)" }}>
              {r.agent_id}: {r.status === "error" ? r.detail : r.status}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function AgentsTab({ surveyId, onChanged }) {
  const [agents, setAgents] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [showLibraryPicker, setShowLibraryPicker] = useState(false);
  const [showProposer, setShowProposer] = useState(false);
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
        <button className="btn" onClick={() => setShowProposer((v) => !v)}>
          {showProposer ? "Cancel" : "Describe what you need"}
        </button>
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

      {showProposer && (
        <AgentProposer
          surveyId={surveyId}
          onApproved={() => {
            setShowProposer(false);
            refresh();
          }}
          onCancel={() => setShowProposer(false)}
        />
      )}

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
        {["agents", "knowledge", "results", "analytics"].map((t) => (
          <button
            key={t}
            className="btn"
            style={tab === t ? { borderColor: "var(--amber)", color: "var(--amber)" } : {}}
            onClick={() => setTab(t)}
          >
            {{ agents: "Agents", knowledge: "Knowledge", results: "Results", analytics: "Analytics" }[t]}
          </button>
        ))}
      </div>

      {tab === "agents" && <AgentsTab surveyId={surveyId} />}
      {tab === "knowledge" && <KnowledgeTab surveyId={surveyId} />}
      {tab === "results" && <ResultsTab surveyId={surveyId} refreshKey={resultsKey} />}
      {tab === "analytics" && <AnalyticsTab surveyId={surveyId} refreshKey={resultsKey} />}
    </div>
  );
}
