import { getLoginUrl } from "../api";

export default function Header({ authenticated }) {
  return (
    <header className="app-header">
      <div className="header-left">
        <h1>📬 Email Priority Classifier</h1>
        <p className="subtitle">Powered by fine-tuned BERT — 99.7% accuracy</p>
      </div>

      <div className="header-right">
        {authenticated ? (
          <span className="auth-badge connected">✓ Gmail Connected</span>
        ) : (
          <a className="connect-btn" href={getLoginUrl()}>
            Connect Gmail
          </a>
        )}
      </div>
    </header>
  );
}
