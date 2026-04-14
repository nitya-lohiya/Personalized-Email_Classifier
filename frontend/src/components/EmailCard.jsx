function formatDate(dateStr) {
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    });
  } catch {
    return dateStr;
  }
}

function cleanSender(from) {
  // "Name <email@x.com>" → "Name"
  const match = from?.match(/^(.*?)\s*<.*>$/);
  return match ? match[1].replace(/"/g, "") : from;
}

export default function EmailCard({ email, onClick }) {
  const confidencePct = (email.confidence * 100).toFixed(0);

  return (
    <div
      className={`email-card priority-${email.priority.toLowerCase()}`}
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && onClick()}
    >
      <div className="email-header">
        <span className="email-subject">{email.subject || "(no subject)"}</span>
        <span className="email-confidence">{confidencePct}%</span>
      </div>

      <div className="email-meta">
        <span className="email-from">{cleanSender(email.from)}</span>
        <span className="email-date">{formatDate(email.date)}</span>
      </div>

      <div className="email-body">{email.body || email.snippet}</div>
    </div>
  );
}
