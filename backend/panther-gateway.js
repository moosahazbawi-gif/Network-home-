const express = require("express");

const app = express();
app.use(express.json());

const PANTHER_URL = process.env.PANTHER_URL || "http://127.0.0.1:8787";

app.get("/api/panther/health", async (_req, res) => {
  try {
    const r = await fetch(`${PANTHER_URL}/health`);
    res.status(r.status).json(await r.json());
  } catch (err) {
    res.status(503).json({ ok: false, error: "Panther unavailable" });
  }
});

app.post("/api/panther/chat", async (req, res) => {
  if (!req.body || typeof req.body.prompt !== "string" || !req.body.prompt.trim()) {
    return res.status(400).json({ ok: false, error: "prompt is required" });
  }
  try {
    const r = await fetch(`${PANTHER_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: req.body.prompt })
    });
    const data = await r.json();
    res.status(r.status).json(data);
  } catch (err) {
    res.status(503).json({ ok: false, error: "Panther unavailable" });
  }
});

module.exports = app;
