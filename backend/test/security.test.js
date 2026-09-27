const test = require("node:test");
const assert = require("node:assert/strict");
const { requireAuth, requireRole, ensureCsrfToken, requireCsrf } = require("../middleware/auth");

function response() {
  return {
    statusCode: 200,
    body: null,
    status(code) { this.statusCode = code; return this; },
    json(body) { this.body = body; return this; },
    sendStatus(code) { this.statusCode = code; return this; },
    get() { return undefined; }
  };
}

test("requireAuth rejects anonymous requests", () => {
  const res = response();
  let called = false;
  requireAuth({ session: {} }, res, () => { called = true; });
  assert.equal(res.statusCode, 401);
  assert.equal(called, false);
});

test("requireRole rejects the wrong role", () => {
  const res = response();
  let called = false;
  requireRole("admin")({ session: { user: { role: "user" } } }, res, () => { called = true; });
  assert.equal(res.statusCode, 403);
  assert.equal(called, false);
});

test("CSRF token is generated server-side and required", () => {
  const req = { session: {}, get() { return this.token; } };
  ensureCsrfToken(req, {}, () => {});
  assert.match(req.session.csrfToken, /^[a-f0-9]{64}$/);

  const bad = response();
  req.token = "bad";
  requireCsrf(req, bad, () => {});
  assert.equal(bad.statusCode, 403);

  const good = response();
  req.token = req.session.csrfToken;
  let called = false;
  requireCsrf(req, good, () => { called = true; });
  assert.equal(called, true);
});
