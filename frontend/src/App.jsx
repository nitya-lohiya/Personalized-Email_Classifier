import { useEffect, useState } from "react";
import Header from "./components/Header";
import Controls from "./components/Controls";
import EmailGrid from "./components/EmailGrid";
import EmailModal from "./components/EmailModal";
import {
  fetchAuthStatus,
  fetchTestDataClassified,
  fetchGmailEmails,
} from "./api";
import "./App.css";

export default function App() {
  const [source, setSource] = useState("test"); // "test" | "gmail"
  const [emails, setEmails] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [authenticated, setAuthenticated] = useState(false);
  const [selectedEmail, setSelectedEmail] = useState(null);

  // On mount: check auth status and handle OAuth redirect
  useEffect(() => {
    fetchAuthStatus()
      .then((s) => setAuthenticated(s.authenticated))
      .catch(() => setAuthenticated(false));

    // If we just returned from the OAuth flow, switch to Gmail view.
    const params = new URLSearchParams(window.location.search);
    if (params.get("auth") === "success") {
      setSource("gmail");
      window.history.replaceState({}, "", "/");
    } else if (params.get("auth") === "error") {
      setError(`Gmail auth failed: ${params.get("message") || "unknown"}`);
      window.history.replaceState({}, "", "/");
    }
  }, []);

  // Fetch emails whenever the source changes
  useEffect(() => {
    loadEmails();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [source]);

  async function loadEmails() {
    setLoading(true);
    setError(null);
    try {
      const data =
        source === "test"
          ? await fetchTestDataClassified()
          : await fetchGmailEmails(100);
      // Sort newest first within the whole list — columns filter downstream
      data.sort((a, b) => new Date(b.date) - new Date(a.date));
      setEmails(data);
    } catch (err) {
      setError(err.message);
      setEmails([]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <Header authenticated={authenticated} />

      <main className="main-content">
        <Controls
          source={source}
          setSource={setSource}
          onRefresh={loadEmails}
          loading={loading}
          emailCount={emails.length}
        />

        <EmailGrid
          emails={emails}
          loading={loading}
          error={error}
          onEmailClick={setSelectedEmail}
        />
      </main>

      {selectedEmail && (
        <EmailModal email={selectedEmail} onClose={() => setSelectedEmail(null)} />
      )}

    </div>
  );
}
