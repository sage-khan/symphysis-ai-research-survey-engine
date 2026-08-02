import { useEffect, useState } from "react";
import { api } from "../api.js";

const DEFAULT_DENYLIST = [
  "ignore (all|any|the) (previous|prior|above) instructions",
  "sk-[A-Za-z0-9]{20,}",
  "-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
];

function blankForm() {
  return {
    agent_id: "",
    role: "",
    role_description: "",
    instrument: "bwm",
    model: { provider: "ollama", name: "", temperature: 0.7, max_tokens: 1024, top_p: 1.0, seed: 42 },
    rag: { enabled: false, corpus_path: "", top_k: 5 },
    sampling: { repeats: 3, max_retries_on_malformed: 2, agreement_threshold: 0.0 },
    permissions: { data_scopes: [], allowed_providers: null, max_cost_usd: null },
    guardrails: { denylist_patterns: DEFAULT_DENYLIST },
    tools: [],
  };
}

export default function AgentForm({ surveyId, existing, onSaved, onCancel }) {
  const [form, setForm] = useState(existing || blankForm());
  const [providers, setProviders] = useState([]);
  const [ollamaModels, setOllamaModels] = useState([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const isEdit = Boolean(existing);

  useEffect(() => {
    api.listProviders().then(setProviders);
    api.listOllamaModels().then((r) => setOllamaModels(r.models || []));
  }, []);

  function set(path, value) {
    setForm((prev) => {
      const next = structuredClone(prev);
      let obj = next;
      const keys = path.split(".");
      for (let i = 0; i < keys.length - 1; i++) obj = obj[keys[i]];
      obj[keys[keys.length - 1]] = value;
      return next;
    });
  }

  async function handleSave() {
    setBusy(true);
    setError(null);
    try {
      if (!form.agent_id || !form.role || !form.model.name) {
        throw new Error("agent_id, role, and model.name are required.");
      }
      const body = {
        ...form,
        model: { ...form.model, seed: form.model.seed === "" ? null : Number(form.model.seed) },
        rag: { ...form.rag, corpus_path: form.rag.enabled ? form.rag.corpus_path : null },
        permissions: {
          ...form.permissions,
          allowed_providers: form.permissions.allowed_providers || [form.model.provider],
        },
      };
      if (isEdit) {
        await api.updateAgent(surveyId, form.agent_id, body);
      } else {
        await api.createAgent(surveyId, body);
      }
      onSaved();
    } catch (err) {
      setError(String(err.message || err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="panel" style={{ padding: 24, marginBottom: 24 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 20 }}>
        <h3>{isEdit ? `Edit ${existing.agent_id}` : "New agent"}</h3>
        <button className="btn" onClick={onCancel}>
          Close
        </button>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 16 }}>
        <label>
          <div className="mono-dim">Agent ID</div>
          <input
            value={form.agent_id}
            onChange={(e) => set("agent_id", e.target.value)}
            disabled={isEdit}
            style={{ width: "100%" }}
          />
        </label>
        <label>
          <div className="mono-dim">Role</div>
          <input value={form.role} onChange={(e) => set("role", e.target.value)} style={{ width: "100%" }} />
        </label>
      </div>

      <label style={{ display: "block", marginBottom: 16 }}>
        <div className="mono-dim">Role description / professional persona</div>
        <textarea
          value={form.role_description}
          onChange={(e) => set("role_description", e.target.value)}
          rows={3}
          style={{ width: "100%" }}
        />
      </label>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 16 }}>
        <label>
          <div className="mono-dim">Provider</div>
          <select value={form.model.provider} onChange={(e) => set("model.provider", e.target.value)} style={{ width: "100%" }}>
            {providers.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </label>
        <label>
          <div className="mono-dim">Model name</div>
          {form.model.provider === "ollama" && ollamaModels.length > 0 ? (
            <select value={form.model.name} onChange={(e) => set("model.name", e.target.value)} style={{ width: "100%" }}>
              <option value="">select a model...</option>
              {ollamaModels.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          ) : (
            <input
              value={form.model.name}
              onChange={(e) => set("model.name", e.target.value)}
              placeholder={form.model.provider === "manual" ? "gemini-2.5-pro" : "model name"}
              style={{ width: "100%" }}
            />
          )}
        </label>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 16 }}>
        <label>
          <div className="mono-dim">Temperature</div>
          <input
            type="number"
            step="0.1"
            value={form.model.temperature}
            onChange={(e) => set("model.temperature", Number(e.target.value))}
            style={{ width: "100%" }}
          />
        </label>
        <label>
          <div className="mono-dim">Max tokens</div>
          <input
            type="number"
            value={form.model.max_tokens}
            onChange={(e) => set("model.max_tokens", Number(e.target.value))}
            style={{ width: "100%" }}
          />
        </label>
        <label>
          <div className="mono-dim">Seed</div>
          <input value={form.model.seed ?? ""} onChange={(e) => set("model.seed", e.target.value)} style={{ width: "100%" }} />
        </label>
        <label>
          <div className="mono-dim">Repeats (samples)</div>
          <input
            type="number"
            value={form.sampling.repeats}
            onChange={(e) => set("sampling.repeats", Number(e.target.value))}
            style={{ width: "100%" }}
          />
        </label>
      </div>

      <label style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
        <input type="checkbox" checked={form.rag.enabled} onChange={(e) => set("rag.enabled", e.target.checked)} />
        <span>RAG-augmented (give this agent a domain corpus)</span>
      </label>
      {form.rag.enabled && (
        <label style={{ display: "block", marginBottom: 16 }}>
          <div className="mono-dim">Corpus path (relative to repo root)</div>
          <input
            value={form.rag.corpus_path || ""}
            onChange={(e) => set("rag.corpus_path", e.target.value)}
            placeholder={`surveys/${surveyId}/rag_corpora/${form.agent_id || "<agent-id>"}`}
            style={{ width: "100%" }}
          />
        </label>
      )}

      <label style={{ display: "block", marginBottom: 16 }}>
        <div className="mono-dim">Denylist patterns (one regex per line, guardrail scan)</div>
        <textarea
          value={form.guardrails.denylist_patterns.join("\n")}
          onChange={(e) => set("guardrails.denylist_patterns", e.target.value.split("\n").filter(Boolean))}
          rows={3}
          style={{ width: "100%" }}
        />
      </label>

      {error && (
        <div className="mono-dim" style={{ color: "var(--red)", marginBottom: 12 }}>
          {error}
        </div>
      )}

      <button className="btn btn-primary" onClick={handleSave} disabled={busy}>
        {isEdit ? "Save changes" : "Create agent"}
      </button>
    </div>
  );
}
