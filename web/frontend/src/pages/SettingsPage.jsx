import { useEffect, useState } from "react";
import { api } from "../api.js";

const API_PROVIDERS = [
  { key: "anthropic", label: "Anthropic (Claude)" },
  { key: "openai", label: "OpenAI (ChatGPT)" },
  { key: "openrouter", label: "OpenRouter" },
  { key: "groq", label: "Groq" },
  { key: "gemini", label: "Gemini" },
  { key: "xai", label: "xAI (Grok)" },
];

function OllamaEndpointSettings() {
  const [presets, setPresets] = useState({});
  const [mode, setMode] = useState("local"); // preset key, or "custom"
  const [baseUrl, setBaseUrl] = useState("");
  const [timeoutSeconds, setTimeoutSeconds] = useState(900);
  const [newPresetLabel, setNewPresetLabel] = useState("");
  const [saved, setSaved] = useState(null);
  const [testResult, setTestResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  async function refresh() {
    const current = await api.getLlmSettings();
    setPresets(current.presets || {});
    setBaseUrl(current.ollama_base_url);
    setTimeoutSeconds(current.ollama_timeout_seconds);
    const matchedPreset = Object.entries(current.presets || {}).find(([, url]) => url === current.ollama_base_url);
    setMode(matchedPreset ? matchedPreset[0] : "custom");
    setSaved(current);
  }

  useEffect(() => {
    refresh();
  }, []);

  function choosePreset(key) {
    setMode(key);
    setTestResult(null);
    if (key !== "custom" && presets[key]) setBaseUrl(presets[key]);
  }

  async function handleTest() {
    setBusy(true);
    setError(null);
    setTestResult(null);
    try {
      setTestResult(await api.testLlmEndpoint(baseUrl));
    } catch (err) {
      setError(String(err.message || err));
    } finally {
      setBusy(false);
    }
  }

  async function handleSave() {
    setBusy(true);
    setError(null);
    try {
      const body = { ollama_base_url: baseUrl, ollama_timeout_seconds: Number(timeoutSeconds) };
      if (mode === "custom" && newPresetLabel.trim()) body.save_preset_label = newPresetLabel.trim();
      const result = await api.saveLlmSettings(body);
      setSaved(result);
      setPresets(result.presets || {});
      setNewPresetLabel("");
    } catch (err) {
      setError(String(err.message || err));
    } finally {
      setBusy(false);
    }
  }

  async function handleDeletePreset(key) {
    if (!confirm(`Remove saved endpoint "${key}"?`)) return;
    const remaining = await api.deletePreset(key);
    setPresets(remaining);
    if (mode === key) setMode("custom");
  }

  const isDirty = saved && (saved.ollama_base_url !== baseUrl || saved.ollama_timeout_seconds !== Number(timeoutSeconds));

  return (
    <div className="panel" style={{ padding: 24, maxWidth: 640, marginBottom: 24 }}>
      <h3 style={{ marginBottom: 4 }}>Ollama endpoint</h3>
      <div className="mono-dim" style={{ marginBottom: 18 }}>
        Everything else (guardrails, the Bayesian solve, storage, reporting) always runs on this
        machine. Only the <code>provider: ollama</code> HTTP calls go wherever this points --
        "Local" for Ollama running on this same machine, or save any remote host (your own server,
        a lab machine, anything reachable) under a label of your choosing to keep LLM compute off
        this machine while you iterate.
      </div>

      <div style={{ display: "flex", gap: 8, marginBottom: 18, flexWrap: "wrap" }}>
        {Object.keys(presets).map((key) => (
          <div key={key} style={{ display: "flex", alignItems: "center" }}>
            <button
              className="btn"
              style={mode === key ? { borderColor: "var(--amber)", color: "var(--amber)" } : {}}
              onClick={() => choosePreset(key)}
            >
              {key === "local" ? "Local" : key}
            </button>
            {key !== "local" && (
              <button className="btn btn-danger" style={{ marginLeft: -1, padding: "8px 10px" }} onClick={() => handleDeletePreset(key)}>
                ×
              </button>
            )}
          </div>
        ))}
        <button
          className="btn"
          style={mode === "custom" ? { borderColor: "var(--amber)", color: "var(--amber)" } : {}}
          onClick={() => choosePreset("custom")}
        >
          Remote / custom
        </button>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 140px", gap: 12, marginBottom: 12 }}>
        <label>
          <div className="mono-dim">Base URL</div>
          <input
            value={baseUrl}
            onChange={(e) => {
              setBaseUrl(e.target.value);
              setMode("custom");
              setTestResult(null);
            }}
            placeholder="http://localhost:11434"
            style={{ width: "100%" }}
          />
        </label>
        <label>
          <div className="mono-dim">Timeout (s)</div>
          <input
            type="number"
            min="1"
            value={timeoutSeconds}
            onChange={(e) => setTimeoutSeconds(e.target.value)}
            style={{ width: "100%" }}
          />
        </label>
      </div>

      {mode === "custom" && (
        <label style={{ display: "block", marginBottom: 18 }}>
          <div className="mono-dim">Save this endpoint as a named preset (optional)</div>
          <input
            value={newPresetLabel}
            onChange={(e) => setNewPresetLabel(e.target.value)}
            placeholder="e.g. my-lab-server"
            style={{ width: "100%" }}
          />
        </label>
      )}

      <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 16 }}>
        <button className="btn" onClick={handleTest} disabled={busy || !baseUrl}>
          Test connection
        </button>
        <button className="btn btn-primary" onClick={handleSave} disabled={busy || !baseUrl}>
          Save
        </button>
        {!isDirty && saved && (
          <span className="mono-dim" style={{ color: "var(--green)" }}>
            Saved -- active for the next run
          </span>
        )}
      </div>

      {testResult && (
        <div
          className="mono-dim"
          style={{
            padding: 12,
            border: `1px solid ${testResult.reachable ? "var(--green)" : "var(--red)"}`,
            borderRadius: "var(--radius)",
            marginBottom: 8,
          }}
        >
          {testResult.reachable ? (
            <>
              <div style={{ color: "var(--green)" }}>Reachable -- {testResult.models.length} model(s) pulled</div>
              <div style={{ marginTop: 6 }}>{testResult.models.join(", ") || "(no models pulled yet)"}</div>
            </>
          ) : (
            <div style={{ color: "var(--red)" }}>Unreachable: {testResult.error}</div>
          )}
        </div>
      )}

      {error && (
        <div className="mono-dim" style={{ color: "var(--red)" }}>
          {error}
        </div>
      )}
    </div>
  );
}

function ApiKeySettings({ title, description, keyProviders }) {
  const [status, setStatus] = useState({});
  const [values, setValues] = useState({});
  const [saved, setSaved] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  async function refresh() {
    setStatus(await api.getApiKeyStatus());
  }

  useEffect(() => {
    refresh();
  }, []);

  async function handleSave() {
    setBusy(true);
    setError(null);
    setSaved(false);
    try {
      const result = await api.saveApiKeys(values);
      setStatus(result);
      setValues({});
      setSaved(true);
    } catch (err) {
      setError(String(err.message || err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="panel" style={{ padding: 24, maxWidth: 640, marginBottom: 24 }}>
      <h3 style={{ marginBottom: 4 }}>{title}</h3>
      <div className="mono-dim" style={{ marginBottom: 18 }}>
        {description}
      </div>

      {keyProviders.map((p) => (
        <label key={p.key} style={{ display: "block", marginBottom: 14 }}>
          <div className="mono-dim">
            {p.label} {status[p.key] && <span style={{ color: "var(--green)" }}>-- key configured</span>}
          </div>
          <input
            type="password"
            value={values[p.key] ?? ""}
            onChange={(e) => setValues((v) => ({ ...v, [p.key]: e.target.value }))}
            placeholder={status[p.key] ? "•••••••• (leave blank to keep current key)" : "paste API key"}
            style={{ width: "100%" }}
          />
        </label>
      ))}

      <div style={{ display: "flex", gap: 8, alignItems: "center", marginTop: 8 }}>
        <button className="btn btn-primary" onClick={handleSave} disabled={busy || Object.keys(values).length === 0}>
          Save keys
        </button>
        {saved && <span className="mono-dim" style={{ color: "var(--green)" }}>Saved</span>}
      </div>

      {error && (
        <div className="mono-dim" style={{ color: "var(--red)", marginTop: 8 }}>
          {error}
        </div>
      )}
    </div>
  );
}

const BASE_URL_PROVIDERS = [
  { key: "openrouter", label: "OpenRouter" },
  { key: "groq", label: "Groq" },
  { key: "gemini", label: "Gemini" },
  { key: "xai", label: "xAI (Grok)" },
];

function ConfigSettings() {
  const [cfg, setCfg] = useState(null);
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState(null);

  async function refresh() {
    setCfg(await api.getAppConfig());
  }

  useEffect(() => {
    refresh();
  }, []);

  function setPath(path, value) {
    setCfg((prev) => {
      const next = structuredClone(prev);
      let obj = next;
      const keys = path.split(".");
      for (let i = 0; i < keys.length - 1; i++) obj = obj[keys[i]];
      obj[keys[keys.length - 1]] = value;
      return next;
    });
    setSaved(false);
  }

  async function handleSave() {
    setBusy(true);
    setError(null);
    try {
      const updated = await api.saveAppConfig(cfg);
      setCfg(updated);
      setSaved(true);
    } catch (err) {
      setError(String(err.message || err));
    } finally {
      setBusy(false);
    }
  }

  if (!cfg) return null;

  return (
    <div className="panel" style={{ padding: 24, maxWidth: 640, marginBottom: 24 }}>
      <h3 style={{ marginBottom: 4 }}>Config -- defaults for new agents</h3>
      <div className="mono-dim" style={{ marginBottom: 18 }}>
        Nothing here is hardcoded in the app: this is{" "}
        <code>config/defaults.yaml</code>, editable here or by editing that
        file directly. Changes apply to newly-created agents and providers;
        existing agents keep whatever values their card already has.
      </div>

      <div className="mono-dim" style={{ marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.04em" }}>
        Hosted-provider base URLs
      </div>
      {BASE_URL_PROVIDERS.map((p) => (
        <label key={p.key} style={{ display: "block", marginBottom: 12 }}>
          <div className="mono-dim">{p.label}</div>
          <input
            value={cfg.provider_base_urls?.[p.key] || ""}
            onChange={(e) => setPath(`provider_base_urls.${p.key}`, e.target.value)}
            style={{ width: "100%" }}
          />
        </label>
      ))}

      <div className="mono-dim" style={{ margin: "18px 0 8px", textTransform: "uppercase", letterSpacing: "0.04em" }}>
        Default model hyperparameters
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 18 }}>
        <label>
          <div className="mono-dim">Temperature</div>
          <input
            type="number"
            step="0.1"
            value={cfg.model_defaults?.temperature ?? 0.7}
            onChange={(e) => setPath("model_defaults.temperature", Number(e.target.value))}
            style={{ width: "100%" }}
          />
        </label>
        <label>
          <div className="mono-dim">Max tokens</div>
          <input
            type="number"
            value={cfg.model_defaults?.max_tokens ?? 1024}
            onChange={(e) => setPath("model_defaults.max_tokens", Number(e.target.value))}
            style={{ width: "100%" }}
          />
        </label>
        <label>
          <div className="mono-dim">Top P</div>
          <input
            type="number"
            step="0.1"
            value={cfg.model_defaults?.top_p ?? 1.0}
            onChange={(e) => setPath("model_defaults.top_p", Number(e.target.value))}
            style={{ width: "100%" }}
          />
        </label>
        <label>
          <div className="mono-dim">Seed</div>
          <input
            value={cfg.model_defaults?.seed ?? ""}
            onChange={(e) => setPath("model_defaults.seed", e.target.value === "" ? null : Number(e.target.value))}
            style={{ width: "100%" }}
          />
        </label>
      </div>

      <div className="mono-dim" style={{ marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.04em" }}>
        Default sampling
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12, marginBottom: 18 }}>
        <label>
          <div className="mono-dim">Repeats</div>
          <input
            type="number"
            value={cfg.sampling_defaults?.repeats ?? 3}
            onChange={(e) => setPath("sampling_defaults.repeats", Number(e.target.value))}
            style={{ width: "100%" }}
          />
        </label>
        <label>
          <div className="mono-dim">Max retries on malformed</div>
          <input
            type="number"
            value={cfg.sampling_defaults?.max_retries_on_malformed ?? 2}
            onChange={(e) => setPath("sampling_defaults.max_retries_on_malformed", Number(e.target.value))}
            style={{ width: "100%" }}
          />
        </label>
        <label>
          <div className="mono-dim">Agreement threshold</div>
          <input
            type="number"
            step="0.1"
            value={cfg.sampling_defaults?.agreement_threshold ?? 0.0}
            onChange={(e) => setPath("sampling_defaults.agreement_threshold", Number(e.target.value))}
            style={{ width: "100%" }}
          />
        </label>
      </div>

      <div className="mono-dim" style={{ marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.04em" }}>
        Default RAG
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12, marginBottom: 12 }}>
        <label>
          <div className="mono-dim">Top K</div>
          <input
            type="number"
            value={cfg.rag_defaults?.top_k ?? 5}
            onChange={(e) => setPath("rag_defaults.top_k", Number(e.target.value))}
            style={{ width: "100%" }}
          />
        </label>
        <label>
          <div className="mono-dim">Chunk size</div>
          <input
            type="number"
            value={cfg.rag_defaults?.chunk_size ?? 800}
            onChange={(e) => setPath("rag_defaults.chunk_size", Number(e.target.value))}
            style={{ width: "100%" }}
          />
        </label>
        <label>
          <div className="mono-dim">Chunk overlap</div>
          <input
            type="number"
            value={cfg.rag_defaults?.chunk_overlap ?? 100}
            onChange={(e) => setPath("rag_defaults.chunk_overlap", Number(e.target.value))}
            style={{ width: "100%" }}
          />
        </label>
      </div>
      <label style={{ display: "block", marginBottom: 18 }}>
        <div className="mono-dim">Embedding model</div>
        <input
          value={cfg.rag_defaults?.embedding_model || ""}
          onChange={(e) => setPath("rag_defaults.embedding_model", e.target.value)}
          style={{ width: "100%" }}
        />
      </label>

      <div className="mono-dim" style={{ marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.04em" }}>
        Default guardrail denylist (one regex per line)
      </div>
      <textarea
        value={(cfg.guardrail_default_denylist || []).join("\n")}
        onChange={(e) => setPath("guardrail_default_denylist", e.target.value.split("\n").filter(Boolean))}
        rows={3}
        style={{ width: "100%", marginBottom: 18 }}
      />

      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
        <button className="btn btn-primary" onClick={handleSave} disabled={busy}>
          Save config
        </button>
        {saved && <span className="mono-dim" style={{ color: "var(--green)" }}>Saved</span>}
      </div>

      {error && (
        <div className="mono-dim" style={{ color: "var(--red)", marginTop: 8 }}>
          {error}
        </div>
      )}
    </div>
  );
}

export default function SettingsPage() {
  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <h1>Settings</h1>
        <div className="mono-dim" style={{ marginTop: 6 }}>
          Where agents send their completions, local and hosted
        </div>
      </div>

      <OllamaEndpointSettings />
      <ApiKeySettings
        title="Hosted-provider API keys"
        description={
          <>
            Lets agents use hosted models (Claude, ChatGPT, OpenRouter, Groq, Gemini, Grok) in
            addition to local Ollama models. Keys are stored on this machine only (gitignored,{" "}
            <code>web/backend/data/llm_settings.json</code>), applied to the running process, and
            never sent back to the browser once saved -- only whether a key is currently set is
            shown.
          </>
        }
        keyProviders={API_PROVIDERS}
      />
      <ApiKeySettings
        title="Web search"
        description={
          <>
            Lets an agent with <code>web_search</code> in its Agent Card's tools look things up
            live instead of relying only on its own training data or a static RAG corpus. Backed by{" "}
            <a href="https://tavily.com" target="_blank" rel="noreferrer">
              Tavily
            </a>
            , an API built for LLM-agent search. Without a key here, any agent granted
            <code> web_search</code> simply proceeds without search results (logged, not
            fabricated) rather than failing.
          </>
        }
        keyProviders={[{ key: "tavily", label: "Tavily" }]}
      />
      <ConfigSettings />
    </div>
  );
}
