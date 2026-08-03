import { useEffect, useState } from "react";
import { api } from "../api.js";
import AgentForm from "../components/AgentForm.jsx";

function shortDid(did) {
  if (!did) return "";
  return did.length > 28 ? `${did.slice(0, 20)}…${did.slice(-6)}` : did;
}

export default function AgentLibraryPage() {
  const [agents, setAgents] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null);
  const [loading, setLoading] = useState(true);

  async function refresh() {
    setLoading(true);
    setAgents(await api.listLibraryAgents());
    setLoading(false);
  }

  useEffect(() => {
    refresh();
  }, []);

  async function handleDelete(agentId) {
    if (!confirm(`Delete library agent "${agentId}"? This does not affect any survey it's already been assigned to.`)) return;
    await api.deleteLibraryAgent(agentId);
    refresh();
  }

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 28 }}>
        <div>
          <h1>Agent Library</h1>
          <div className="mono-dim" style={{ marginTop: 6 }}>
            {agents.length} reusable agent{agents.length === 1 ? "" : "s"}: assign any of these to a survey from
            that survey's Agents tab, or create new ones here
          </div>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => {
            setEditing(null);
            setShowForm(true);
          }}
        >
          + New agent
        </button>
      </div>

      {showForm && (
        <AgentForm
          scope="library"
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
              <th>Display name</th>
              <th>Agent</th>
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
                <td>{a.display_name || <span className="mono-dim">-</span>}</td>
                <td>{a.agent_id}</td>
                <td>
                  {a.role}
                  {a.expertise && <div className="mono-dim">{a.expertise}</div>}
                </td>
                <td>
                  {a.provider}/{a.model}
                </td>
                <td>{a.rag_enabled ? "yes" : "-"}</td>
                <td>{a.tools && a.tools.length ? a.tools.join(", ") : "-"}</td>
                <td className="mono-dim" title={a.did}>
                  {shortDid(a.did)}
                </td>
                <td style={{ textAlign: "right", whiteSpace: "nowrap" }}>
                  <button
                    className="btn"
                    onClick={async () => {
                      setEditing(await api.getLibraryAgent(a.agent_id));
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
            {!loading && agents.length === 0 && (
              <tr>
                <td colSpan={8} className="mono-dim">
                  No library agents yet. Create one, or add one from an existing survey's Agents tab
                  (not yet supported; library agents currently start here).
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
