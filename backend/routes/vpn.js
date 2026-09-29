const express = require("express");
const rateLimit = require("express-rate-limit");
const Stripe = require("stripe");
const { pool } = require("../db");
const { requireCsrf, ensureCsrfToken } = require("../middleware/auth");
const { ACTIVATION_CENTS, getOrCreateTrial, getStatus, normalizeEmail, isValidEmail } = require("../vpn-service");

const router = express.Router();
const activationLimiter = rateLimit({ windowMs: 15 * 60 * 1000, limit: 10, standardHeaders: true, legacyHeaders: false });

function stripeClient() {
  if (!process.env.STRIPE_SECRET_KEY) throw new Error("Stripe is not configured");
  return new Stripe(process.env.STRIPE_SECRET_KEY);
}

router.get("/csrf", ensureCsrfToken, (req, res) => res.json({ ok: true, csrfToken: req.session.csrfToken }));

router.post("/trial", activationLimiter, requireCsrf, async (req, res, next) => {
  try {
    const email = normalizeEmail(req.body?.email);
    if (!isValidEmail(email)) return res.status(400).json({ ok: false, error: "valid email is required" });
    const row = await getOrCreateTrial(email);
    res.json({ ok: true, email: row.email, ...getStatus(row), activationPriceUsd: ACTIVATION_CENTS / 100 });
  } catch (err) { next(err); }
});

router.get("/status", async (req, res, next) => {
  try {
    const email = normalizeEmail(req.query?.email);
    if (!isValidEmail(email)) return res.status(400).json({ ok: false, error: "valid email is required" });
    const result = await pool.query("SELECT email, status, trial_ends_at, active_until FROM vpn_customers WHERE email = $1 LIMIT 1", [email]);
    res.json({ ok: true, email, ...getStatus(result.rows[0]) });
  } catch (err) { next(err); }
});

router.post("/checkout", activationLimiter, requireCsrf, async (req, res, next) => {
  try {
    const email = normalizeEmail(req.body?.email);
    if (!isValidEmail(email)) return res.status(400).json({ ok: false, error: "valid email is required" });
    const customer = await getOrCreateTrial(email);
    if (getStatus(customer).state === "active") return res.status(409).json({ ok: false, error: "VPN service is already active" });
    const stripe = stripeClient();
    const origin = process.env.PUBLIC_APP_URL;
    if (!origin) return res.status(503).json({ ok: false, error: "PUBLIC_APP_URL is not configured" });
    const session = await stripe.checkout.sessions.create({
      mode: "payment",
      customer_email: email,
      client_reference_id: String(customer.id),
      line_items: [{ price_data: { currency: "usd", product_data: { name: "PX2.VPN — Service Activation" }, unit_amount: ACTIVATION_CENTS }, quantity: 1 }],
      metadata: { vpn_customer_id: String(customer.id), service: "PX2.VPN" },
      success_url: `${origin}/panther-vpn/?payment=success&session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${origin}/panther-vpn/?payment=cancelled`
    });
    await pool.query("UPDATE vpn_customers SET stripe_checkout_session_id = $1, updated_at = NOW() WHERE id = $2", [session.id, customer.id]);
    res.json({ ok: true, url: session.url });
  } catch (err) { next(err); }
});

module.exports = router;
