export default function Controls({ source, setSource, onRefresh, loading, emailCount }) {
  return (
    <div className="controls">
      <div className="source-toggle">
        <button
          className={source === "test" ? "active" : ""}
          onClick={() => setSource("test")}
        >
          Sample Data
        </button>
        <button
          className={source === "gmail" ? "active" : ""}
          onClick={() => setSource("gmail")}
        >
          My Gmail
        </button>
      </div>

      <div className="controls-right">
        <span className="email-total">{emailCount} emails</span>
        <button className="refresh-btn" onClick={onRefresh} disabled={loading}>
          {loading ? "Loading…" : "Refresh"}
        </button>
      </div>
    </div>
  );
}
