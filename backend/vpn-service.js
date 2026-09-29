const crypto = require("crypto");
const { pool } = require("./db");

const TRIAL_DAYS = 3;
const ACTIVATION_CENTS = 200;

function normalizeEmail(value) {
  return typeof value === "string" ? value.trim().toLowerCase() : "";
}

function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function trialEndsAt(startedAt) {
  return new Date(new Date(startedAt).getTime() + TRIAL_DAYS * 24 * 60 * 60 * 1000);
}

function getStatus(row, now = new Date()) {
  if (!row) return { state: "not_started", trialEndsAt: null, activeUntil: null };
  const current = new Date(now);
  if (row.status === "active" && (!row.active_until || new Date(row.active_until) > current)) {
    return { state: "active", trialEndsAt: row.trial_ends_at, activeUntil: row.active_until };
  }
  if (row.trial_ends_at && new Date(row.trial_ends_at) > current) {
    return { state: "trial", trialEndsAt: row.trial_ends_at, activeUntil: null };
  }
  return { state: row.status === "active" ? "expired" : "expired", trialEndsAt: row.trial_ends_at, activeUntil: row.active_until };
}

async function getOrCreateTrial(email) {
  const normalized = normalizeEmail(email);
  if (!isValidEmail(normalized)) throw new Error("valid email is required");

  const existing = await pool.query(
    "SELECT id, email, status, trial_started_at, trial_ends_at, active_until, stripe_checkout_session_id FROM vpn_customers WHERE email = $1 LIMIT 1",
    [normalized]
  );
  if (existing.rowCount) return existing.rows[0];

  const token = crypto.randomBytes(24).toString("hex");
  const result = await pool.query(
    `INSERT INTO vpn_customers
      (email, status, trial_started_at, trial_ends_at, access_token)
     VALUES ($1, 'trial', NOW(), NOW() + INTERVAL '3 days', $2)
     RETURNING id, email, status, trial_started_at, trial_ends_at, active_until, stripe_checkout_session_id`,
    [normalized, token]
  );
  return result.rows[0];
}

module.exports = {
  TRIAL_DAYS,
  ACTIVATION_CENTS,
  normalizeEmail,
  isValidEmail,
  trialEndsAt,
  getStatus,
  getOrCreateTrial
};
