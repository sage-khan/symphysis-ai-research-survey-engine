const BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

async function request(path, options = {}) {
  const resp = await fetch(`${BASE}${path}`, {
    headers: options.body instanceof FormData ? undefined : { "Content-Type": "application/json" },
    ...options,
  });
  if (!resp.ok) {
    let detail = resp.statusText;
    try {
      const data = await resp.json();
      detail = data.detail || JSON.stringify(data);
    } catch {
      // response wasn't JSON, keep statusText
    }
    throw new Error(detail);
  }
  const contentType = resp.headers.get("content-type") || "";
  if (contentType.includes("application/json")) return resp.json();
  return resp;
}

export const api = {
  listSurveys: () => request("/api/surveys"),
  getSurvey: (id) => request(`/api/surveys/${id}`),
  createSurvey: (body) => request("/api/surveys", { method: "POST", body: JSON.stringify(body) }),
  renameSurvey: (id, title) => request(`/api/surveys/${id}`, { method: "PATCH", body: JSON.stringify({ title }) }),
  deleteSurvey: (id) => request(`/api/surveys/${id}`, { method: "DELETE" }),
  proposeSurveyConcept: (concept, provider, model) =>
    request("/api/surveys/propose-concept", { method: "POST", body: JSON.stringify({ concept, provider, model }) }),
  parseDocument: (file) => {
    const form = new FormData();
    form.append("file", file);
    return request("/api/surveys/parse", { method: "POST", body: form });
  },
  runSurvey: (id) => request(`/api/surveys/${id}/run`, { method: "POST" }),
  runStatus: (id) => request(`/api/surveys/${id}/run-status`),
  preflight: (id) => request(`/api/surveys/${id}/preflight`),
  getResults: (id) => request(`/api/surveys/${id}/results`),
  getAnalytics: (id) => request(`/api/surveys/${id}/analytics`),
  getIntegrityManifest: (id) => request(`/api/surveys/${id}/integrity`),
  verifyIntegrity: (id) => request(`/api/surveys/${id}/verify-integrity`),
  chartUrl: (surveyId, chartName) => `${BASE}/api/surveys/${surveyId}/charts/${chartName}`,
  downloadUrl: (id) => `${BASE}/api/surveys/${id}/download`,

  listProviders: () => request("/api/providers"),
  listModelsForProvider: (provider) => request(`/api/models/${provider}`),
  listRolePacks: () => request("/api/role-packs"),

  getLlmSettings: () => request("/api/settings/llm"),
  saveLlmSettings: (body) => request("/api/settings/llm", { method: "PUT", body: JSON.stringify(body) }),
  deletePreset: (label) => request(`/api/settings/llm/presets/${encodeURIComponent(label)}`, { method: "DELETE" }),
  testLlmEndpoint: (baseUrl) =>
    request(`/api/settings/llm/test${baseUrl ? `?base_url=${encodeURIComponent(baseUrl)}` : ""}`),

  getApiKeyStatus: () => request("/api/settings/api-keys"),
  saveApiKeys: (body) => request("/api/settings/api-keys", { method: "PUT", body: JSON.stringify(body) }),

  getAppConfig: () => request("/api/settings/config"),
  saveAppConfig: (body) => request("/api/settings/config", { method: "PUT", body: JSON.stringify(body) }),

  getGlobalRulefile: () => request("/api/settings/global-rulefile"),
  saveGlobalRulefile: (content) =>
    request("/api/settings/global-rulefile", { method: "PUT", body: JSON.stringify({ content }) }),

  listAgents: (surveyId) => request(`/api/surveys/${surveyId}/agents`),
  getAgent: (surveyId, agentId) => request(`/api/surveys/${surveyId}/agents/${agentId}`),
  createAgent: (surveyId, body) => request(`/api/surveys/${surveyId}/agents`, { method: "POST", body: JSON.stringify(body) }),
  updateAgent: (surveyId, agentId, body) =>
    request(`/api/surveys/${surveyId}/agents/${agentId}`, { method: "PUT", body: JSON.stringify(body) }),
  deleteAgent: (surveyId, agentId) => request(`/api/surveys/${surveyId}/agents/${agentId}`, { method: "DELETE" }),
  getTrace: (surveyId, agentId) => request(`/api/surveys/${surveyId}/agents/${agentId}/trace`),

  listLibraryAgents: () => request("/api/library/agents"),
  getLibraryAgent: (agentId) => request(`/api/library/agents/${agentId}`),
  createLibraryAgent: (body) => request("/api/library/agents", { method: "POST", body: JSON.stringify(body) }),
  updateLibraryAgent: (agentId, body) =>
    request(`/api/library/agents/${agentId}`, { method: "PUT", body: JSON.stringify(body) }),
  deleteLibraryAgent: (agentId) => request(`/api/library/agents/${agentId}`, { method: "DELETE" }),
  assignLibraryAgentToSurvey: (agentId, surveyId) =>
    request(`/api/library/agents/${agentId}/assign/${surveyId}`, { method: "POST" }),

  proposeAgents: (surveyId, body) =>
    request(`/api/surveys/${surveyId}/propose-agents`, { method: "POST", body: JSON.stringify(body) }),
  approveAgents: (surveyId, proposals) =>
    request(`/api/surveys/${surveyId}/approve-agents`, { method: "POST", body: JSON.stringify({ proposals }) }),

  listKnowledgeFiles: (surveyId) => request(`/api/surveys/${surveyId}/knowledge`),
  uploadKnowledgeFile: (surveyId, file) => {
    const form = new FormData();
    form.append("file", file);
    return request(`/api/surveys/${surveyId}/knowledge`, { method: "POST", body: form });
  },
  deleteKnowledgeFile: (surveyId, filename) =>
    request(`/api/surveys/${surveyId}/knowledge/${encodeURIComponent(filename)}`, { method: "DELETE" }),

  getSurveyRulefile: (surveyId) => request(`/api/surveys/${surveyId}/rulefile`),
  saveSurveyRulefile: (surveyId, content) =>
    request(`/api/surveys/${surveyId}/rulefile`, { method: "PUT", body: JSON.stringify({ content }) }),

  listKnowledgeBases: () => request("/api/knowledge-bases"),
  createKnowledgeBase: (body) => request("/api/knowledge-bases", { method: "POST", body: JSON.stringify(body) }),
  deleteKnowledgeBase: (kbId) => request(`/api/knowledge-bases/${kbId}`, { method: "DELETE" }),
  uploadKnowledgeBaseFile: (kbId, file) => {
    const form = new FormData();
    form.append("file", file);
    return request(`/api/knowledge-bases/${kbId}/files`, { method: "POST", body: form });
  },
  deleteKnowledgeBaseFile: (kbId, filename) =>
    request(`/api/knowledge-bases/${kbId}/files/${encodeURIComponent(filename)}`, { method: "DELETE" }),
};
