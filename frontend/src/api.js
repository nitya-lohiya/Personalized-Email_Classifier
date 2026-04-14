const API_BASE = "http://localhost:8000";

export async function fetchHealth() {
  const r = await fetch(`${API_BASE}/health`);
  return r.json();
}

export async function fetchAuthStatus() {
  const r = await fetch(`${API_BASE}/auth/status`);
  return r.json();
}

export function getLoginUrl() {
  return `${API_BASE}/auth/login`;
}

export async function fetchTestDataClassified() {
  // 1. Get sample emails
  const testRes = await fetch(`${API_BASE}/test_data`);
  const testData = await testRes.json();
  const samples = testData.sample_emails;

  // 2. Classify them via /classify_batch
  const batchRes = await fetch(`${API_BASE}/classify_batch`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ emails: samples.map((s) => s.text) }),
  });
  if (!batchRes.ok) throw new Error("Failed to classify test data");
  const batchData = await batchRes.json();

  // 3. Merge into a unified email shape
  return samples.map((sample, i) => ({
    id: `test-${i}`,
    subject: sample.text.slice(0, 60),
    from: "Sample Data",
    date: new Date().toISOString(),
    snippet: sample.text,
    body: sample.text,
    priority: batchData.predictions[i].priority,
    confidence: batchData.predictions[i].confidence,
  }));
}

export async function fetchGmailEmails(maxResults = 15) {
  const r = await fetch(`${API_BASE}/emails/gmail?max_results=${maxResults}`);
  if (r.status === 401) {
    throw new Error("Not authenticated with Gmail");
  }
  if (!r.ok) {
    const err = await r.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(err.detail || "Failed to fetch Gmail emails");
  }
  const data = await r.json();
  return data.emails.map((e) => ({
    ...e,
    body: e.body || e.snippet,
  }));
}
