const crypto = require("crypto");

function requireAuth(req, res, next) {
  if (!req.session || !req.session.user) {
    return res.status(401).json({ ok: false, error: "authentication required" });
  }
  next();
}

function requireRole(role) {
  return (req, res, next) => {
    if (!req.session || !req.session.user) {
      return res.status(401).json({ ok: false, error: "authentication required" });
    }
    if (req.session.user.role !== role) {
      return res.status(403).json({ ok: false, error: "forbidden" });
    }
    next();
  };
}

function ensureCsrfToken(req, _res, next) {
  if (!req.session.csrfToken) {
    req.session.csrfToken = crypto.randomBytes(32).toString("hex");
  }
  next();
}

function requireCsrf(req, res, next) {
  const supplied = req.get("X-CSRF-Token");
  const expected = req.session && req.session.csrfToken;

  if (!supplied || !expected) {
    return res.status(403).json({ ok: false, error: "csrf validation failed" });
  }

  const a = Buffer.from(supplied);
  const b = Buffer.from(expected);
  if (a.length !== b.length || !crypto.timingSafeEqual(a, b)) {
    return res.status(403).json({ ok: false, error: "csrf validation failed" });
  }

  next();
}

module.exports = { requireAuth, requireRole, ensureCsrfToken, requireCsrf };
