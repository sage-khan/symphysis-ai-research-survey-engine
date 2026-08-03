import { useEffect, useState } from "react";
import { api } from "../api.js";
import StatusDot from "../components/StatusDot.jsx";

function formatDate(iso) {
  if (!iso) return "-";
  try {
    return new Date(iso).toISOString().slice(0, 16).replace("T", " ") + " UTC";
  } catch {
    return iso;
  }
}

function slugify(s) {
  return s
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
}

function NewSurveyPanel({ onCreated, onClose }) {
  const [mode, setMode] = useState("upload"); // "upload" | "manual"
  const [id, setId] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [instrument, setInstrument] = useState("bwm");
  const [candidates, setCandidates] = useState([{ code: "", label: "" }]);
  const [warnings, setWarnings] = useState([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  async function handleFile(e) {
    const file = e.target.files[0];
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      const parsed = await api.parseDocument(file);
      setId(parsed.id || slugify(file.name.replace(/\.[^.]+$/, "")));
      setTitle(parsed.title || file.name);
      if (parsed.instrument) setInstrument(parsed.instrument);
      setCandidates(parsed.candidates.length ? parsed.candidates : [{ code: "", label: "" }]);
      setWarnings(parsed.warnings || []);
    } catch (err) {
      setError(String(err.message || err));
    } finally {
      setBusy(false);
    }
  }

  function updateCandidate(i, field, value) {
    setCandidates((prev) => prev.map((c, idx) => (idx === i ? { ...c, [field]: value } : c)));
  }
  function addCandidate() {
    setCandidates((prev) => [...prev, { code: "", label: "" }]);
  }
  function removeCandidate(i) {
    setCandidates((prev) => prev.filter((_, idx) => idx !== i));
  }

  async function handleCreate() {
    setBusy(true);
    setError(null);
    try {
      const criteria = candidates.filter((c) => c.code.trim() && c.label.trim());
      if (!criteria.length) throw new Error("At least one criterion with a code and label is required.");
      await api.createSurvey({ id: id || slugify(title), title: title || id, description, instrument, criteria });
      onCreated();
    } catch (err) {
      setError(String(err.message || err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="panel" style={{ padding: 24, marginBottom: 28 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 20 }}>
        <h3>New survey</h3>
        <button className="btn" onClick={onClose}>
          Close
        </button>
      </div>

      <div style={{ display: "flex", gap: 8, marginBottom: 18 }}>
        <button
          className="btn"
          style={mode === "upload" ? { borderColor: "var(--amber)", color: "var(--amber)" } : {}}
          onClick={() => setMode("upload")}
        >
          Upload document
        </button>
        <button
          className="btn"
          style={mode === "manual" ? { borderColor: "var(--amber)", color: "var(--amber)" } : {}}
          onClick={() => setMode("manual")}
        >
          Enter manually
        </button>
      </div>

      {mode === "upload" && (
        <div style={{ marginBottom: 18 }}>
          <input type="file" accept=".md,.markdown,.lss,.xml,.pdf,.docx" onChange={handleFile} disabled={busy} />
          <div className="mono-dim" style={{ marginTop: 6 }}>
            .md (structured, well-supported) · .lss (LimeSurvey export) · .pdf / .docx (best-effort, review candidates)
          </div>
        </div>
      )}

      {warnings.length > 0 && (
        <div style={{ marginBottom: 16, padding: 12, border: "1px solid var(--amber-dim)", borderRadius: "var(--radius)" }}>
          {warnings.map((w, i) => (
            <div key={i} className="mono-dim" style={{ color: "var(--amber)" }}>
              ⚠ {w}
            </div>
          ))}
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 160px", gap: 12, marginBottom: 18 }}>
        <label>
          <div className="mono-dim">Survey ID</div>
          <input value={id} onChange={(e) => setId(slugify(e.target.value))} placeholder="my-survey" style={{ width: "100%" }} />
        </label>
        <label>
          <div className="mono-dim">Title</div>
          <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="My Survey" style={{ width: "100%" }} />
        </label>
        <label>
          <div className="mono-dim">Instrument</div>
          <select value={instrument} onChange={(e) => setInstrument(e.target.value)} style={{ width: "100%" }}>
            <option value="bwm">bwm</option>
          </select>
        </label>
      </div>

      <label style={{ display: "block", marginBottom: 18 }}>
        <div className="mono-dim">Description (optional: what this project is about; shown to agents in their introduction)</div>
        <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={2} style={{ width: "100%" }} />
      </label>

      <div className="mono-dim" style={{ marginBottom: 8 }}>
        Criteria being weighed against each other (edit freely before creating).{" "}
        <strong>Code</strong> is a short technical ID used internally and in charts (e.g. "Q", "PT":
        keep it brief, no spaces). <strong>Label</strong> is the full human-readable name and definition
        shown to agents and in reports (e.g. "Quality: is the data technically sound?").
      </div>
      <table style={{ marginBottom: 12 }}>
        <thead>
          <tr>
            <th style={{ width: 100 }}>Code</th>
            <th>Label (full name / definition)</th>
            <th style={{ width: 40 }} />
          </tr>
        </thead>
        <tbody>
          {candidates.map((c, i) => (
            <tr key={i}>
              <td>
                <input value={c.code} onChange={(e) => updateCandidate(i, "code", e.target.value)} placeholder="e.g. Q" style={{ width: "100%" }} />
              </td>
              <td>
                <input value={c.label} onChange={(e) => updateCandidate(i, "label", e.target.value)} placeholder="e.g. Quality: is the data technically sound?" style={{ width: "100%" }} />
              </td>
              <td>
                <button className="btn btn-danger" onClick={() => removeCandidate(i)}>
                  ×
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <button className="btn" onClick={addCandidate} style={{ marginBottom: 20 }}>
        + Add criterion
      </button>

      {error && (
        <div className="mono-dim" style={{ color: "var(--red)", marginBottom: 12 }}>
          {error}
        </div>
      )}

      <div>
        <button className="btn btn-primary" onClick={handleCreate} disabled={busy}>
          Create survey
        </button>
      </div>
    </div>
  );
}

export default function SurveysPage({ onOpenSurvey }) {
  const [surveys, setSurveys] = useState([]);
  const [showNew, setShowNew] = useState(false);
  const [loading, setLoading] = useState(true);

  async function refresh() {
    setLoading(true);
    setSurveys(await api.listSurveys());
    setLoading(false);
  }

  useEffect(() => {
    refresh();
  }, []);

  async function handleDelete(id) {
    if (!confirm(`Delete survey "${id}"? This removes all its agents and results.`)) return;
    await api.deleteSurvey(id);
    refresh();
  }

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 28 }}>
        <div>
          <h1>Surveys</h1>
          <div className="mono-dim" style={{ marginTop: 6 }}>
            {surveys.length} survey{surveys.length === 1 ? "" : "s"}
          </div>
        </div>
        <button className="btn btn-primary" onClick={() => setShowNew((v) => !v)}>
          {showNew ? "Cancel" : "+ New survey"}
        </button>
      </div>

      {showNew && (
        <NewSurveyPanel
          onCreated={() => {
            setShowNew(false);
            refresh();
          }}
          onClose={() => setShowNew(false)}
        />
      )}

      {loading ? (
        <div className="mono-dim">Loading...</div>
      ) : surveys.length === 0 ? (
        <div className="panel" style={{ padding: 40, textAlign: "center" }}>
          <div className="mono-dim">No surveys yet. Create one to get started.</div>
        </div>
      ) : (
        <div className="panel">
          <table>
            <thead>
              <tr>
                <th>Title</th>
                <th>Created</th>
                <th>Instrument</th>
                <th>Agents</th>
                <th>Status</th>
                <th>Results</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {surveys.map((s) => (
                <tr key={s.id}>
                  <td>
                    <a href="#" onClick={(e) => { e.preventDefault(); onOpenSurvey(s.id); }} style={{ color: "var(--text)" }}>
                      <strong>{s.title}</strong>
                    </a>
                    <div className="mono-dim">{s.id}</div>
                  </td>
                  <td className="mono-dim">{formatDate(s.created_at)}</td>
                  <td>{s.instrument}</td>
                  <td>{s.agent_count}</td>
                  <td>
                    <StatusDot status={s.run_status} />
                  </td>
                  <td>{s.has_results ? "yes" : "-"}</td>
                  <td style={{ textAlign: "right" }}>
                    <button className="btn" onClick={() => onOpenSurvey(s.id)} style={{ marginRight: 8 }}>
                      Open
                    </button>
                    <button className="btn btn-danger" onClick={() => handleDelete(s.id)}>
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
