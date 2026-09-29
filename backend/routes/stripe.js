const express = require("express");
const Stripe = require("stripe");
const { pool } = require("../db");
const router = express.Router();

router.post("/webhook", express.raw({ type: "application/json" }), async (req, res) => {
  if (!process.env.STRIPE_SECRET_KEY || !process.env.STRIPE_WEBHOOK_SECRET) return res.status(503).send("Stripe webhook is not configured");
  const stripe = new Stripe(process.env.STRIPE_SECRET_KEY);
  let event;
  try {
    event = stripe.webhooks.constructEvent(req.body, req.headers["stripe-signature"], process.env.STRIPE_WEBHOOK_SECRET);
  } catch (err) {
    return res.status(400).send(`Webhook signature verification failed: ${err.message}`);
  }
  try {
    if (event.type === "checkout.session.completed") {
      const session = event.data.object;
      if (session.payment_status === "paid" && session.metadata?.service === "PX2.VPN") {
        const customerId = Number(session.metadata.vpn_customer_id);
        if (Number.isSafeInteger(customerId) && customerId > 0) {
          await pool.query(`UPDATE vpn_customers SET status='active', active_until=NOW()+INTERVAL '30 days', stripe_payment_intent_id=$1, updated_at=NOW() WHERE id=$2`, [session.payment_intent || null, customerId]);
        }
      }
    }
    return res.json({ received: true });
  } catch (err) {
    console.error("stripe webhook error:", err.message);
    return res.status(500).send("webhook processing failed");
  }
});
module.exports = router;
