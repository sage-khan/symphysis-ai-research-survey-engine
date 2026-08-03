import { useEffect, useState } from "react";
import { api } from "../api.js";

// Emergency fallback only, used if /api/settings/config can't be reached
// before this form mounts. The real source of truth is the backend's
// config/defaults.yaml (see Settings -> Config), not this constant --
// once that request resolves, blankForm(cfg) below uses the fetched
// values instead.
const FALLBACK_DENYLIST = [
  "ignore (all|any|the) (previous|prior|above) instructions",
  "sk-[A-Za-z0-9]{20,}",
  "-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
];

function blankForm(cfg = {}) {
  const model = cfg.model_defaults || {};
  const sampling = cfg.sampling_defaults || {};
  const rag = cfg.rag_defaults || {};
  const denylist = cfg.guardrail_default_denylist;
  return {
    agent_id: "",
    display_name: "",
    expertise: "",
    role_pack: null,
    role: "",
    role_description: "",
    system_prompt_override: "",
    instrument: "bwm",
    model: {
      provider: "ollama",
      name: "",
      temperature: model.temperature ?? 0.7,
      max_tokens: model.max_tokens ?? 1024,
      top_p: model.top_p ?? 1.0,
      seed: model.seed ?? 42,
    },
    rag: { enabled: false, corpus_path: "", top_k: rag.top_k ?? 5 },
    sampling: {
      repeats: sampling.repeats ?? 3,
      max_retries_on_malformed: sampling.max_retries_on_malformed ?? 2,
      agreement_threshold: sampling.agreement_threshold ?? 0.0,
    },
    permissions: { data_scopes: [], allowed_providers: null, max_cost_usd: null },
    guardrails: { denylist_patterns: denylist && denylist.length ? denylist : FALLBACK_DENYLIST },
    tools: [],
  };
}

export default function AgentForm({ surveyId, scope = "survey", existing, onSaved, onCancel }) {
  const [form, setForm] = useState(existing || blankForm());
  const [providers, setProviders] = useState([]);
  const [modelCatalog, setModelCatalog] = useState({ models: [], error: null });
  const [rolePacks, setRolePacks] = useState([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const isEdit = Boolean(existing);

  useEffect(() => {
    api.listProviders().then(setProviders);
    api.listRolePacks().then(setRolePacks).catch(() => setRolePacks([]));
    if (!isEdit) {
      api.getAppConfig().then((cfg) => setForm(blankForm(cfg))).catch(() => {});
    }
  }, []);

  // Re-fetch the real, live model list every time the provider changes --
  // never a hardcoded or remembered list, since a hosted provider's
  // catalog (or whether its API key is even configured) can change.
  useEffect(() => {
    const provider = form.model.provider;
    if (provider === "manual") {
      setModelCatalog({ models: [], error: null });
      return;
    }
    api.listModelsForProvider(provider).then(setModelCatalog);
  }, [form.model.provider]);

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
      if (scope === "library") {
        if (isEdit) await api.updateLibraryAgent(form.agent_id, body);
        else await api.createLibraryAgent(body);
      } else if (isEdit) {
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
        <h3>{isEdit ? `Edit ${existing.agent_id}` : scope === "library" ? "New library agent" : "New agent"}</h3>
        <button className="btn" onClick={onCancel}>
          Close
        </button>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12, marginBottom: 16 }}>
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
          <div className="mono-dim">Display name</div>
          <input
            value={form.display_name || ""}
            onChange={(e) => set("display_name", e.target.value)}
            placeholder={form.role || "shown in the UI instead of the agent ID"}
            style={{ width: "100%" }}
          />
        </label>
        <label>
          <div className="mono-dim">Role</div>
          <input value={form.role} onChange={(e) => set("role", e.target.value)} style={{ width: "100%" }} />
        </label>
      </div>

      <label style={{ display: "block", marginBottom: 16 }}>
        <div className="mono-dim">Profession / expertise (short)</div>
        <input
          value={form.expertise || ""}
          onChange={(e) => set("expertise", e.target.value)}
          placeholder="e.g. Structural engineering, ISO 25012 data quality, 15 years construction industry"
          style={{ width: "100%" }}
        />
      </label>

      <label style={{ display: "block", marginBottom: 16 }}>
        <div className="mono-dim">Standard role knowledge pack (optional)</div>
        <select
          value={form.role_pack || ""}
          onChange={(e) => set("role_pack", e.target.value || null)}
          style={{ width: "100%" }}
        >
          <option value="">none</option>
          {rolePacks.map((p) => (
            <option key={p.id} value={p.id}>
              {p.label}
            </option>
          ))}
        </select>
        <div className="mono-dim" style={{ marginTop: 4 }}>
          {form.role_pack
            ? rolePacks.find((p) => p.id === form.role_pack)?.summary
            : "Attaches a curated professional-domain primer (standards, evaluation heuristics, common failure modes) as extra context on every run, so this agent speaks from that standpoint immediately instead of from role_description alone."}
        </div>
      </label>

      <label style={{ display: "block", marginBottom: 16 }}>
        <div className="mono-dim">Role description / professional persona</div>
        <textarea
          value={form.role_description}
          onChange={(e) => set("role_description", e.target.value)}
          rows={3}
          style={{ width: "100%" }}
        />
      </label>

      <label style={{ display: "block", marginBottom: 16 }}>
        <div className="mono-dim">System prompt (leave blank to use the survey's shared default template)</div>
        <textarea
          value={form.system_prompt_override || ""}
          onChange={(e) => set("system_prompt_override", e.target.value || null)}
          rows={4}
          placeholder="Overrides the shared template just for this agent. Plain text -- no {role}/{role_description} substitution here, write it out directly."
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
          {modelCatalog.models.length > 0 ? (
            <select value={form.model.name} onChange={(e) => set("model.name", e.target.value)} style={{ width: "100%" }}>
              <option value="">select a model...</option>
              {modelCatalog.models.map((m) => (
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
          {form.model.provider !== "manual" && modelCatalog.error && (
            <div className="mono-dim" style={{ color: "var(--amber)", marginTop: 4 }}>
              ⚠ Couldn't fetch {form.model.provider}'s real model list ({modelCatalog.error}) -- typing a model name
              here is not validated against anything real.
            </div>
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
            placeholder={
              scope === "library"
                ? `agents_library/rag_corpora/${form.agent_id || "<agent-id>"}`
                : `surveys/${surveyId}/rag_corpora/${form.agent_id || "<agent-id>"}`
            }
            style={{ width: "100%" }}
          />
          {scope === "library" && (
            <div className="mono-dim" style={{ marginTop: 4 }}>
              A RAG corpus set here travels with this agent wherever it's assigned. Make sure the
              path exists before running a survey it's assigned to (this form doesn't upload files).
            </div>
          )}
        </label>
      )}

      <div className="mono-dim" style={{ marginBottom: 8 }}>
        Tools
      </div>
      <label style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
        <input
          type="checkbox"
          checked={form.tools.includes("web_search")}
          onChange={(e) =>
            set("tools", e.target.checked ? [...form.tools, "web_search"] : form.tools.filter((t) => t !== "web_search"))
          }
        />
        <span>Web search (real-time lookup via Tavily -- configure the API key in Settings)</span>
      </label>
      <div className="mono-dim" style={{ marginBottom: 16 }}>
        Every agent in a survey automatically has access to that survey's shared knowledge
        repository (Knowledge tab) with no separate toggle -- same as a project's shared reference
        material for a human panel.
      </div>

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
