const express = require("express");
const rateLimit = require("express-rate-limit");
const { pool } = require("../db");
const { verifyPassword } = require("../auth");
const { requireCsrf, ensureCsrfToken } = require("../middleware/auth");

const router = express.Router();

const loginLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  limit: 10,
  standardHeaders: true,
  legacyHeaders: false,
  message: { ok: false, error: "too many login attempts; try again later" }
});

router.get("/csrf", ensureCsrfToken, (req, res) => {
  res.json({ ok: true, csrfToken: req.session.csrfToken });
});

router.post("/login", loginLimiter, requireCsrf, async (req, res, next) => {
  try {
    const username = typeof req.body?.username === "string" ? req.body.username.trim() : "";
    const password = typeof req.body?.password === "string" ? req.body.password : "";

    if (!username || !password) {
      return res.status(400).json({ ok: false, error: "username and password are required" });
    }

    const result = await pool.query(
      "SELECT id, username, password_hash, role FROM users WHERE username = $1 LIMIT 1",
      [username]
    );
    const user = result.rows[0];

    if (!user || !(await verifyPassword(password, user.password_hash))) {
      return res.status(401).json({ ok: false, error: "invalid credentials" });
    }

    await new Promise((resolve, reject) => {
      req.session.regenerate((err) => (err ? reject(err) : resolve()));
    });

    req.session.user = {
      id: user.id,
      username: user.username,
      role: user.role
    };

    req.session.csrfToken = require("crypto").randomBytes(32).toString("hex");

    await new Promise((resolve, reject) => {
      req.session.save((err) => (err ? reject(err) : resolve()));
    });

    res.json({
      ok: true,
      user: req.session.user,
      csrfToken: req.session.csrfToken
    });
  } catch (err) {
    next(err);
  }
});

router.get("/me", (req, res) => {
  if (!req.session?.user) {
    return res.status(401).json({ ok: false, error: "authentication required" });
  }
  res.json({ ok: true, user: req.session.user });
});

router.get("/check", (req, res) => {
  if (!req.session?.user) return res.sendStatus(401);
  res.sendStatus(204);
});

router.post("/logout", requireCsrf, (req, res, next) => {
  req.session.destroy((err) => {
    if (err) return next(err);
    res.clearCookie("nh.sid", { httpOnly: true, sameSite: "lax", secure: process.env.NODE_ENV === "production" });
    res.json({ ok: true });
  });
});

module.exports = router;
