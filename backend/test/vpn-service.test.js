const test = require("node:test");
const assert = require("node:assert/strict");
const { TRIAL_DAYS, ACTIVATION_CENTS, normalizeEmail, isValidEmail, trialEndsAt, getStatus } = require("../vpn-service");

test("PX2.VPN commercial rules are fixed", () => {
  assert.equal(TRIAL_DAYS, 3);
  assert.equal(ACTIVATION_CENTS, 200);
});

test("email normalization and validation", () => {
  assert.equal(normalizeEmail("  Mo@Example.COM "), "mo@example.com");
  assert.equal(isValidEmail("mo@example.com"), true);
  assert.equal(isValidEmail("not-an-email"), false);
});

test("trial expiration is exactly three days", () => {
  const start = new Date("2026-09-30T00:00:00Z");
  assert.equal(trialEndsAt(start).toISOString(), "2026-10-03T00:00:00.000Z");
});

test("status transitions from trial to expired and active", () => {
  const now = new Date("2026-09-30T00:00:00Z");
  assert.equal(getStatus({ status:"trial", trial_ends_at:"2026-10-01T00:00:00Z", active_until:null }, now).state, "trial");
  assert.equal(getStatus({ status:"trial", trial_ends_at:"2026-09-29T00:00:00Z", active_until:null }, now).state, "expired");
  assert.equal(getStatus({ status:"active", trial_ends_at:"2026-09-29T00:00:00Z", active_until:"2027-09-30T00:00:00Z" }, now).state, "active");
});
