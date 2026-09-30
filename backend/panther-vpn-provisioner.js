const crypto = require("crypto");

const DEFAULT_TIMEOUT_MS = 15000;

function getProvisionUrl() {
  const value = process.env.PANTHER_PROVISION_URL;
  if (!value) throw new Error("PANTHER_PROVISION_URL is not configured");
  const url = new URL(value);
  if (!["http:", "https:"].includes(url.protocol)) throw new Error("PANTHER_PROVISION_URL must use HTTP or HTTPS");
  return url;
}

function sign(secret, timestamp, body) {
  return crypto.createHmac("sha256", secret).update(`${timestamp}.${body}`).digest("hex");
}

async function provisionVpn({ customerId, email, activeUntil }) {
  const secret = process.env.PANTHER_PROVISION_SECRET;
  if (!secret || secret.length < 32) throw new Error("PANTHER_PROVISION_SECRET must be at least 32 characters");

  const body = JSON.stringify({
    request_id: crypto.randomUUID(),
    customer_id: customerId,
    email,
    active_until: new Date(activeUntil).toISOString()
  });
  const timestamp = String(Math.floor(Date.now() / 1000));
  const response = await fetch(getProvisionUrl(), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-PX2-Timestamp": timestamp,
      "X-PX2-Signature": sign(secret, timestamp, body)
    },
    body,
    signal: AbortSignal.timeout(Number(process.env.PANTHER_PROVISION_TIMEOUT_MS || DEFAULT_TIMEOUT_MS))
  });

  const text = await response.text();
  let data;
  try { data = JSON.parse(text); } catch { data = null; }
  if (!response.ok || !data?.ok) {
    throw new Error(data?.error || `Panther provisioning failed (HTTP ${response.status})`);
  }
  return data;
}

module.exports = { provisionVpn, sign };
