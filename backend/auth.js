const argon2 = require("argon2");
const { pool } = require("./db");

const MIN_PASSWORD_LENGTH = 12;

async function hashPassword(password) {
  if (typeof password !== "string" || password.length < MIN_PASSWORD_LENGTH) {
    throw new Error(`Password must be at least ${MIN_PASSWORD_LENGTH} characters`);
  }
  return argon2.hash(password, { type: argon2.argon2id });
}

async function verifyPassword(password, hash) {
  if (typeof password !== "string" || typeof hash !== "string") return false;
  try {
    return await argon2.verify(hash, password);
  } catch {
    return false;
  }
}

async function bootstrapAdmin() {
  const username = (process.env.ADMIN_USER || "").trim();
  const password = process.env.ADMIN_PASSWORD || "";

  if (!username || !password) {
    throw new Error("ADMIN_USER and ADMIN_PASSWORD are required");
  }
  if (password.length < MIN_PASSWORD_LENGTH) {
    throw new Error(`ADMIN_PASSWORD must be at least ${MIN_PASSWORD_LENGTH} characters`);
  }

  const existing = await pool.query(
    "SELECT id FROM users WHERE username = $1 LIMIT 1",
    [username]
  );

  if (existing.rowCount > 0) return false;

  const passwordHash = await hashPassword(password);
  await pool.query(
    "INSERT INTO users (username, password_hash, role) VALUES ($1, $2, 'admin')",
    [username, passwordHash]
  );
  return true;
}

module.exports = { MIN_PASSWORD_LENGTH, hashPassword, verifyPassword, bootstrapAdmin };
