const { Pool } = require("pg");

const pool = new Pool(
  process.env.DATABASE_URL
    ? { connectionString: process.env.DATABASE_URL, ssl: process.env.PGSSL === "true" ? { rejectUnauthorized: process.env.PGSSL_REJECT_UNAUTHORIZED !== "false" } : false }
    : {
        host: process.env.PGHOST || "127.0.0.1",
        port: Number(process.env.PGPORT || 5432),
        user: process.env.PGUSER || "network_home",
        password: process.env.PGPASSWORD,
        database: process.env.PGDATABASE || "network_home"
      }
);

async function initDb() {
  await pool.query(`
    CREATE TABLE IF NOT EXISTS users (
      id BIGSERIAL PRIMARY KEY,
      username TEXT NOT NULL UNIQUE,
      password_hash TEXT NOT NULL,
      role TEXT NOT NULL DEFAULT 'admin' CHECK (role IN ('admin')),
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS customer_requests (
      id BIGSERIAL PRIMARY KEY,
      name TEXT NOT NULL,
      phone TEXT NOT NULL,
      service TEXT NOT NULL,
      message TEXT NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS customer_requests_created_at_idx
      ON customer_requests (created_at DESC);

    CREATE TABLE IF NOT EXISTS vpn_customers (
      id BIGSERIAL PRIMARY KEY,
      email TEXT NOT NULL UNIQUE,
      status TEXT NOT NULL DEFAULT 'trial' CHECK (status IN ('trial','active')),
      trial_started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      trial_ends_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '3 days'),
      active_until TIMESTAMPTZ,
      access_token TEXT NOT NULL UNIQUE,
      stripe_checkout_session_id TEXT,
      stripe_payment_intent_id TEXT,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS vpn_customers_status_idx
      ON vpn_customers (status, trial_ends_at, active_until);
  `);
}

async function closeDb() {
  await pool.end();
}

module.exports = { pool, initDb, closeDb };
