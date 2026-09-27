async function getRequests() {
  const response = await fetch("/api/request/", { credentials: "same-origin" });
  if (!response.ok) throw new Error("Unable to load requests");
  const data = await response.json();
  return data.requests || [];
}

async function addRequest(req) {
  const response = await fetch("/api/request", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req)
  });
  if (!response.ok) throw new Error("Unable to save request");
  return response.json();
}

async function clearRequests(csrfToken) {
  const response = await fetch("/api/request/", {
    method: "DELETE",
    credentials: "same-origin",
    headers: { "X-CSRF-Token": csrfToken }
  });
  if (!response.ok) throw new Error("Unable to clear requests");
  return response.json();
}
