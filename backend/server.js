require("dotenv").config();

const express = require("express");
const cors = require("cors");
const helmet = require("helmet");
const session = require("express-session");
const pgSession = require("connect-pg-simple")(session);
const { pool, initDb } = require("./db");
const { bootstrapAdmin } = require("./auth");
const authRoutes = require("./routes/auth");
const requestRoutes = require("./routes/requests");
const pantherGateway = require("./panther-gateway");

const app = express();
const isProduction = process.env.NODE_ENV === "production";

if (!process.env.SESSION_SECRET || process.env.SESSION_SECRET.length < 32) {
  throw new Error("SESSION_SECRET must be at least 32 characters");
}
if (isProduction) app.set("trust proxy", 1);

const allowedOrigins = (process.env.CORS_ORIGIN || "")
  .split(",")
  .map((v) => v.trim())
  .filter(Boolean);

app.disable("x-powered-by");
app.use(helmet());
app.use(cors({
  origin(origin, callback) {
    if (!origin || allowedOrigins.includes(origin)) {
      return callback(null, true);
    }
    return callback(new Error("CORS origin denied"));
  },
  credentials: true,
  methods: ["GET", "POST", "DELETE", "OPTIONS"],
  allowedHeaders: ["Content-Type", "X-CSRF-Token"]
}));
app.use(express.json({ limit: "64kb" }));

app.use(session({
  name: "nh.sid",
  store: new pgSession({
    pool,
    tableName: "user_sessions",
    createTableIfMissing: true
  }),
  secret: process.env.SESSION_SECRET,
  resave: false,
  saveUninitialized: false,
  cookie: {
    httpOnly: true,
    secure: isProduction,
    sameSite: "lax",
    maxAge: 8 * 60 * 60 * 1000
  }
}));

app.get("/health", (_req, res) => res.json({ ok: true, service: "network-home-backend" }));
app.use("/api/auth", authRoutes);
app.use("/api/request", requestRoutes);
app.use(pantherGateway);

app.use((err, _req, res, _next) => {
  if (err?.message === "CORS origin denied") {
    return res.status(403).json({ ok: false, error: "cors origin denied" });
  }
  console.error("request error:", err.message);
  res.status(500).json({ ok: false, error: "internal server error" });
});

async function start() {
  await initDb();
  await bootstrapAdmin();

  const port = Number(process.env.PORT || 3000);
  return app.listen(port, () => {
    console.log(`Network-home server running on :${port}`);
  });
}

if (require.main === module) {
  start().catch((err) => {
    console.error("startup failed:", err.message);
    process.exit(1);
  });
}

module.exports = { app, start };
