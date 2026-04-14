import { useEffect } from "react";

const PRIORITY_ICONS = { High: "🔴", Medium: "🟡", Low: "🟢" };

function formatFullDate(dateStr) {
  try {
    return new Date(dateStr).toLocaleString("en-US", {
      weekday: "long",
      month: "long",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return dateStr;
  }
}

export default function EmailModal({ email, onClose }) {
  useEffect(() => {
    function handleEsc(e) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", handleEsc);
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", handleEsc);
      document.body.style.overflow = "";
    };
  }, [onClose]);

  if (!email) return null;

  const confidencePct = (email.confidence * 100).toFixed(1);

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose} aria-label="Close">
          ✕
        </button>

        <div className={`modal-priority-banner priority-${email.priority.toLowerCase()}`}>
          <span>
            {PRIORITY_ICONS[email.priority]} {email.priority} Priority
          </span>
          <span className="modal-confidence">{confidencePct}% confident</span>
        </div>

        <h2 className="modal-subject">{email.subject || "(no subject)"}</h2>

        <div className="modal-meta">
          <div>
            <span className="meta-label">From</span>
            <span className="meta-value">{email.from}</span>
          </div>
          <div>
            <span className="meta-label">Date</span>
            <span className="meta-value">{formatFullDate(email.date)}</span>
          </div>
        </div>

        <div className="modal-body">
          {email.body || email.snippet || "(no content)"}
        </div>
      </div>
    </div>
  );
}
