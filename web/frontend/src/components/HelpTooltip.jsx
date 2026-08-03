import { useState } from "react";

// A small "?" icon that, on click, pops up a plain-language explanation of
// the input or output it sits next to. Meant for exactly the fields a
// non-technical user would otherwise have to guess at (a jargon term, a
// setting with real behavioral consequences, a number whose meaning isn't
// obvious from its label alone). Click again, or click elsewhere, to close.
export default function HelpTooltip({ children }) {
  const [open, setOpen] = useState(false);

  return (
    <span style={{ position: "relative", display: "inline-block", marginLeft: 6 }}>
      <button
        type="button"
        onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          setOpen((v) => !v);
        }}
        aria-label="What is this?"
        title="What is this?"
        style={{
          width: 16,
          height: 16,
          borderRadius: "50%",
          border: "1px solid var(--border)",
          background: "var(--bg-raised)",
          color: "var(--text-dim)",
          fontSize: 10,
          lineHeight: "14px",
          padding: 0,
          cursor: "pointer",
          verticalAlign: "middle",
        }}
      >
        ?
      </button>
      {open && (
        <>
          <div
            onClick={() => setOpen(false)}
            style={{ position: "fixed", top: 0, left: 0, right: 0, bottom: 0, zIndex: 40 }}
          />
          <div
            className="panel"
            style={{
              position: "absolute",
              top: "calc(100% + 6px)",
              left: 0,
              zIndex: 41,
              width: 280,
              padding: 12,
              fontSize: 12,
              fontWeight: "normal",
              lineHeight: 1.5,
              boxShadow: "0 4px 16px rgba(0,0,0,0.25)",
            }}
          >
            {children}
          </div>
        </>
      )}
    </span>
  );
}
