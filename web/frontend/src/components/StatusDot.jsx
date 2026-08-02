export default function StatusDot({ status }) {
  const label =
    { idle: "idle", running: "running", complete: "complete", error: "error", pending_manual: "awaiting paste" }[status] ||
    status;
  return (
    <span className="tag">
      <span className={`dot dot-${status}`} />
      {label}
    </span>
  );
}
