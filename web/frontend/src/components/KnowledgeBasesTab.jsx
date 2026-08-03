import { useEffect, useRef, useState } from "react";
import { api } from "../api.js";

// Reusable, named domain-knowledge bases: upload files once here, then
// paste the resulting corpus_path into any agent's RAG corpus field (see
// AgentForm's "Or link an existing knowledge base" picker) instead of
// re-uploading the same files into a one-off per-agent corpus every time.
export default function KnowledgeBasesTab() {
  const [kbs, setKbs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newId, setNewId] = useState("");
  const [newName, setNewName] = useState("");
  const [newDescription, setNewDescription] = useState("");
  const [error, setError] = useState(null);
  const [uploadingTo, setUploadingTo] = useState(null);
  const fileInputRef = useRef(null);

  async function refresh() {
    setLoading(true);
    setKbs(await api.listKnowledgeBases());
    setLoading(false);
  }

  useEffect(() => {
    refresh();
  }, []);

  async function handleCreate() {
    setError(null);
    try {
      await api.createKnowledgeBase({ id: newId.trim(), name: newName.trim() || newId.trim(), description: newDescription.trim() });
      setShowCreate(false);
      setNewId("");
      setNewName("");
      setNewDescription("");
      refresh();
    } catch (e) {
      setError(e.message);
    }
  }

  async function handleDelete(kbId) {
    if (!confirm(`Delete knowledge base "${kbId}" and every file in it? Any agent currently pointed at this corpus_path will lose its reference material.`)) return;
    await api.deleteKnowledgeBase(kbId);
    refresh();
  }

  function triggerUpload(kbId) {
    setUploadingTo(kbId);
    fileInputRef.current?.click();
  }

  async function handleFileChosen(e) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file || !uploadingTo) return;
    setError(null);
    try {
      await api.uploadKnowledgeBaseFile(uploadingTo, file);
      refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setUploadingTo(null);
    }
  }

  async function handleDeleteFile(kbId, filename) {
    await api.deleteKnowledgeBaseFile(kbId, filename);
    refresh();
  }

  function copyPath(path) {
    navigator.clipboard?.writeText(path);
  }

  return (
    <div>
      <input ref={fileInputRef} type="file" accept=".md,.markdown,.txt,.pdf,.docx" style={{ display: "none" }} onChange={handleFileChosen} />

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 16 }}>
        <div className="mono-dim">
          {kbs.length} reusable knowledge base{kbs.length === 1 ? "" : "s"}: upload files once, then set any agent's
          RAG corpus_path to one of these (or pick it from the dropdown when editing an agent) to reuse the same
          material without uploading it again.
        </div>
        <button className="btn btn-primary" onClick={() => setShowCreate(true)}>
          + New knowledge base
        </button>
      </div>

      {error && (
        <div className="panel" style={{ marginBottom: 16, color: "var(--red, #d33)" }}>
          {error}
        </div>
      )}

      {showCreate && (
        <div className="panel" style={{ marginBottom: 16 }}>
          <label style={{ display: "block", marginBottom: 12 }}>
            <div className="mono-dim">ID (used in the corpus_path, lowercase-hyphenated)</div>
            <input value={newId} onChange={(e) => setNewId(e.target.value)} placeholder="blockchain-trust" style={{ width: "100%" }} />
          </label>
          <label style={{ display: "block", marginBottom: 12 }}>
            <div className="mono-dim">Display name</div>
            <input value={newName} onChange={(e) => setNewName(e.target.value)} placeholder="Blockchain Trust & Attack Resistance" style={{ width: "100%" }} />
          </label>
          <label style={{ display: "block", marginBottom: 16 }}>
            <div className="mono-dim">Description</div>
            <textarea value={newDescription} onChange={(e) => setNewDescription(e.target.value)} rows={2} style={{ width: "100%" }} />
          </label>
          <button className="btn btn-primary" onClick={handleCreate} disabled={!newId.trim()} style={{ marginRight: 8 }}>
            Create
          </button>
          <button className="btn" onClick={() => setShowCreate(false)}>
            Cancel
          </button>
        </div>
      )}

      {kbs.map((kb) => (
        <div className="panel" key={kb.id} style={{ marginBottom: 16 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 8 }}>
            <div>
              <strong>{kb.name}</strong>
              {kb.description && <div className="mono-dim" style={{ marginTop: 2 }}>{kb.description}</div>}
            </div>
            <div style={{ whiteSpace: "nowrap" }}>
              <button className="btn" onClick={() => triggerUpload(kb.id)} style={{ marginRight: 6 }}>
                Upload file
              </button>
              <button className="btn btn-danger" onClick={() => handleDelete(kb.id)}>
                Delete
              </button>
            </div>
          </div>
          <div className="mono-dim" style={{ marginBottom: 8, display: "flex", alignItems: "center", gap: 8 }}>
            corpus_path: <code>{kb.corpus_path}</code>
            <button className="btn" style={{ padding: "2px 8px" }} onClick={() => copyPath(kb.corpus_path)}>
              Copy
            </button>
          </div>
          <table>
            <thead>
              <tr>
                <th>File</th>
                <th>Size</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {kb.files.map((f) => (
                <tr key={f.filename}>
                  <td>{f.filename}</td>
                  <td className="mono-dim">{f.size_bytes.toLocaleString()} bytes</td>
                  <td style={{ textAlign: "right" }}>
                    <button className="btn btn-danger" onClick={() => handleDeleteFile(kb.id, f.filename)}>
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
              {kb.files.length === 0 && (
                <tr>
                  <td colSpan={3} className="mono-dim">
                    No files yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      ))}

      {!loading && kbs.length === 0 && (
        <div className="panel mono-dim">No knowledge bases yet. Create one to get started.</div>
      )}
    </div>
  );
}
