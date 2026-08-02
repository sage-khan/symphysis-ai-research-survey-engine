import { useEffect, useState } from "react";
import { api } from "../api.js";

const PRESET_LABELS = {
  local: "Local Ollama",
  "veritas-server": "Veritas server (Tailscale)",
};

export default function SettingsPage() {
  const [presets, setPresets] = useState({});
  const [mode, setMode] = useState("local"); // "local" | "veritas-server" | "custom"
  const [baseUrl, setBaseUrl] = useState("");
  const [timeoutSeconds, setTimeoutSeconds] = useState(900);
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
      const result = await api.testLlmEndpoint(baseUrl);
      setTestResult(result);
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
      const result = await api.saveLlmSettings({ ollama_base_url: baseUrl, ollama_timeout_seconds: Number(timeoutSeconds) });
      setSaved(result);
    } catch (err) {
      setError(String(err.message || err));
    } finally {
      setBusy(false);
    }
  }

  const isDirty = saved && (saved.ollama_base_url !== baseUrl || saved.ollama_timeout_seconds !== Number(timeoutSeconds));

  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <h1>Settings</h1>
        <div className="mono-dim" style={{ marginTop: 6 }}>
          Where this app sends its Ollama-backed agents' completions
        </div>
      </div>

      <div className="panel" style={{ padding: 24, maxWidth: 640 }}>
        <h3 style={{ marginBottom: 4 }}>LLM endpoint</h3>
        <div className="mono-dim" style={{ marginBottom: 18 }}>
          Everything else (guardrails, the Bayesian solve, storage, reporting) always runs on
          this machine. Only the <code>provider: ollama</code> HTTP calls go wherever this
          points -- pick the veritas server to keep LLM compute off your machine while you
          iterate locally.
        </div>

        <div style={{ display: "flex", gap: 8, marginBottom: 18, flexWrap: "wrap" }}>
          {Object.keys(presets).map((key) => (
            <button
              key={key}
              className="btn"
              style={mode === key ? { borderColor: "var(--amber)", color: "var(--amber)" } : {}}
              onClick={() => choosePreset(key)}
            >
              {PRESET_LABELS[key] || key}
            </button>
          ))}
          <button
            className="btn"
            style={mode === "custom" ? { borderColor: "var(--amber)", color: "var(--amber)" } : {}}
            onClick={() => choosePreset("custom")}
          >
            Custom
          </button>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 140px", gap: 12, marginBottom: 18 }}>
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
    </div>
  );
}
