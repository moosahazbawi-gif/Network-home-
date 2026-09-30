const express = require("express");
const Stripe = require("stripe");
const { pool } = require("../db");
const { provisionVpn } = require("../panther-vpn-provisioner");
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
          const result = await pool.query(
            `UPDATE vpn_customers
             SET status='active',
                 active_until=NOW()+INTERVAL '1 year',
                 stripe_payment_intent_id=$1,
                 updated_at=NOW()
             WHERE id=$2
             RETURNING id, email, active_until, provisioning_status`,
            [session.payment_intent || null, customerId]
          );
          const customer = result.rows[0];
          if (!customer) return res.status(404).send("VPN customer not found");

          if (customer.provisioning_status !== "provisioned") {
            await pool.query(
              "UPDATE vpn_customers SET provisioning_status='provisioning', updated_at=NOW() WHERE id=$1",
              [customer.id]
            );
            try {
              const provisioned = await provisionVpn({
                customerId: customer.id,
                email: customer.email,
                activeUntil: customer.active_until
              });
              await pool.query(
                `UPDATE vpn_customers
                 SET provisioning_status='provisioned',
                     provisioning_id=$1,
                     client_config_url=$2,
                     provisioned_at=NOW(),
                     provisioning_error=NULL,
                     updated_at=NOW()
                 WHERE id=$3`,
                [provisioned.provisioning_id || null, provisioned.client_config_url || null, customer.id]
              );
            } catch (provisionError) {
              await pool.query(
                "UPDATE vpn_customers SET provisioning_status='failed', provisioning_error=$1, updated_at=NOW() WHERE id=$2",
                [provisionError.message.slice(0, 1000), customer.id]
              );
              console.error("PX2.VPN provisioning failed:", provisionError.message);
              return res.status(502).send("VPN provisioning failed");
            }
          }
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
