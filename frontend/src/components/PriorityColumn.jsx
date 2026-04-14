import EmailCard from "./EmailCard";

const PRIORITY_ICONS = { High: "🔴", Medium: "🟡", Low: "🟢" };

export default function PriorityColumn({ priority, emails, onEmailClick }) {
  return (
    <div className={`priority-column column-${priority.toLowerCase()}`}>
      <div className="column-header">
        <h2>
          {PRIORITY_ICONS[priority]} {priority}
        </h2>
        <span className="email-count">{emails.length}</span>
      </div>

      <div className="email-list">
        {emails.length === 0 ? (
          <div className="empty-state">No {priority.toLowerCase()} priority emails</div>
        ) : (
          emails.map((email) => (
            <EmailCard
              key={email.id}
              email={email}
              onClick={() => onEmailClick(email)}
            />
          ))
        )}
      </div>
    </div>
  );
}
