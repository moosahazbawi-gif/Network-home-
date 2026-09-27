const express = require("express");
const { pool } = require("../db");
const { requireAuth, requireRole, requireCsrf } = require("../middleware/auth");

const router = express.Router();
const publicRequestLimiter = rateLimit({ windowMs: 15 * 60 * 1000, limit: 30, standardHeaders: true, legacyHeaders: false });

function clean(value, max) {
  return typeof value === "string" ? value.trim().slice(0, max) : "";
}

router.post("/", publicRequestLimiter, async (req, res, next) => {
  try {
    const name = clean(req.body?.name, 120);
    const phone = clean(req.body?.phone, 40);
    const service = clean(req.body?.service, 120);
    const message = clean(req.body?.message, 4000);

    if (!name || !phone || !service || !message) {
      return res.status(400).json({ ok: false, error: "name, phone, service and message are required" });
    }

    const result = await pool.query(
      "INSERT INTO customer_requests (name, phone, service, message) VALUES ($1, $2, $3, $4) RETURNING id, name, phone, service, message, created_at",
      [name, phone, service, message]
    );

    res.status(201).json({ ok: true, request: result.rows[0] });
  } catch (err) {
    next(err);
  }
});

router.get("/", requireRole("admin"), async (_req, res, next) => {
  try {
    const result = await pool.query(
      "SELECT id, name, phone, service, message, created_at FROM customer_requests ORDER BY created_at DESC"
    );
    res.json({ ok: true, requests: result.rows });
  } catch (err) {
    next(err);
  }
});

router.delete("/:id", requireRole("admin"), requireCsrf, async (req, res, next) => {
  try {
    const id = Number(req.params.id);
    if (!Number.isSafeInteger(id) || id < 1) {
      return res.status(400).json({ ok: false, error: "invalid request id" });
    }

    const result = await pool.query(
      "DELETE FROM customer_requests WHERE id = $1 RETURNING id",
      [id]
    );
    if (result.rowCount === 0) {
      return res.status(404).json({ ok: false, error: "request not found" });
    }
    res.json({ ok: true });
  } catch (err) {
    next(err);
  }
});

router.delete("/", requireRole("admin"), requireCsrf, async (_req, res, next) => {
  try {
    await pool.query("DELETE FROM customer_requests");
    res.json({ ok: true });
  } catch (err) {
    next(err);
  }
});

module.exports = router;
