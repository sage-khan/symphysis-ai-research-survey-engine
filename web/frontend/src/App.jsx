import { useState } from "react";
import SurveysPage from "./pages/SurveysPage.jsx";
import SurveyDetailPage from "./pages/SurveyDetailPage.jsx";
import AgentLibraryPage from "./pages/AgentLibraryPage.jsx";
import SettingsPage from "./pages/SettingsPage.jsx";

const NAV = [
  { key: "surveys", label: "Surveys", glyph: "01" },
  { key: "library", label: "Agent Library", glyph: "02" },
  { key: "settings", label: "Settings", glyph: "03" },
];

export default function App() {
  const [page, setPage] = useState("surveys"); // "surveys" | "settings"
  const [selectedSurvey, setSelectedSurvey] = useState(null);

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <aside
        style={{
          width: 220,
          flexShrink: 0,
          borderRight: "1px solid var(--border)",
          background: "var(--bg-raised)",
          padding: "28px 20px",
          position: "sticky",
          top: 0,
          height: "100vh",
        }}
      >
        <div style={{ marginBottom: 40 }}>
          <div style={{ fontFamily: "var(--font-display)", fontSize: 26, fontWeight: 700, color: "var(--amber)" }}>
            Symphysis
          </div>
          <div className="mono-dim" style={{ marginTop: 2 }}>AI Research Survey Engine</div>
          <div className="mono-dim" style={{ marginTop: 8, letterSpacing: "0.04em" }}>
            v0.1.0 · control panel
          </div>
        </div>

        <nav>
          {NAV.map((item) => {
            const active = page === item.key && (item.key !== "surveys" || !selectedSurvey);
            return (
              <button
                key={item.key}
                onClick={() => {
                  setPage(item.key);
                  setSelectedSurvey(null);
                }}
                className="btn"
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  width: "100%",
                  justifyContent: "flex-start",
                  marginBottom: 6,
                  border: "none",
                  background: active ? "var(--bg-panel)" : "transparent",
                  color: active ? "var(--amber)" : "var(--text-dim)",
                }}
              >
                <span className="mono-dim">{item.glyph}</span>
                {item.label}
              </button>
            );
          })}
        </nav>

        <div style={{ position: "absolute", bottom: 24, left: 20, right: 20 }}>
          <div className="mono-dim" style={{ lineHeight: 1.7 }}>
            Config-driven agent panels
            <br />
            for expert-elicitation surveys
          </div>
        </div>
      </aside>

      <main style={{ flex: 1, padding: "32px 40px", maxWidth: 1400 }}>
        {page === "settings" ? (
          <SettingsPage />
        ) : page === "library" ? (
          <AgentLibraryPage />
        ) : selectedSurvey ? (
          <SurveyDetailPage surveyId={selectedSurvey} onBack={() => setSelectedSurvey(null)} />
        ) : (
          <SurveysPage onOpenSurvey={setSelectedSurvey} />
        )}
      </main>
    </div>
  );
}
