import PriorityColumn from "./PriorityColumn";

export default function EmailGrid({ emails, loading, error, onEmailClick }) {
  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Classifying emails with BERT...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-container">
        <p>⚠️ {error}</p>
      </div>
    );
  }

  const high = emails.filter((e) => e.priority === "High");
  const medium = emails.filter((e) => e.priority === "Medium");
  const low = emails.filter((e) => e.priority === "Low");

  return (
    <div className="email-grid">
      <PriorityColumn priority="High" emails={high} onEmailClick={onEmailClick} />
      <PriorityColumn priority="Medium" emails={medium} onEmailClick={onEmailClick} />
      <PriorityColumn priority="Low" emails={low} onEmailClick={onEmailClick} />
    </div>
  );
}
