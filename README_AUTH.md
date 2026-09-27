# Network Home Authentication & Security

## Security model

- Passwords use Argon2id.
- Authentication uses server-side PostgreSQL sessions.
- Session cookie: `nh.sid`.
- Cookie: HttpOnly, SameSite=Lax, Secure in production.
- Session lifetime: 8 hours.
- Login regenerates the session ID.
- Logout destroys the server-side session.
- Privileged state is not stored in localStorage.
- Authenticated state-changing requests require CSRF tokens.
- Login is rate-limited.
- CRM reads/deletes require the admin role.
- Panther chat requires admin authorization and CSRF protection.
- Panther health requires authentication.
- Panther upstream is configured server-side; clients cannot select it.
- Helmet security headers are enabled.
- CORS is explicit; wildcard credentialed CORS is not used.
- PostgreSQL stores users, sessions, and customer requests.
- SQL uses parameterized queries.

## Administrator bootstrap

Set `ADMIN_USER` and `ADMIN_PASSWORD` only in the deployment environment.

The bootstrap creates the administrator only if that username does not already exist. It never replaces an existing password on startup.

The administrator password must be at least 12 characters.

Never commit `.env` or real credentials.

## Authentication API

- `GET /api/auth/csrf` — creates/returns a CSRF token for the current browser session.
- `POST /api/auth/login` — validates credentials and regenerates the session.
- `GET /api/auth/me` — returns the current authenticated user.
- `GET /api/auth/check` — session check used by Nginx.
- `POST /api/auth/logout` — destroys the session.

The authenticated session contains only user ID, username and role. The CSRF token is held separately in the server-side session.

## Authorization

- `GET /api/request/` — admin only.
- `DELETE /api/request/:id` — admin + CSRF.
- `DELETE /api/request/` — admin + CSRF.
- `GET /api/panther/health` — authenticated users.
- `POST /api/panther/chat` — admin + CSRF.

Customer submission remains public at `POST /api/request`, with bounded server-side validation.

## Dashboard

The CRM dashboard uses the authenticated session and protected APIs. Nginx should also protect the dashboard resource with an internal `/api/auth/check` subrequest.

## Panther boundary

Network Home is the authenticated gateway. Panther itself is not changed by this authentication layer.

Default Panther upstream:

`http://127.0.0.1:8787`

Clients cannot override the upstream URL.

## Environment

Required runtime values:

- `DATABASE_URL`
- `SESSION_SECRET` (at least 32 characters)
- `ADMIN_USER`
- `ADMIN_PASSWORD` (at least 12 characters)
- `CORS_ORIGIN`
- `PANTHER_URL`

See `.env.example`.

## Security checklist

- No hardcoded `admin/1234`.
- No plaintext administrator password in source.
- No JWT is required for this browser session model.
- No wildcard credentialed CORS.
- No client-side authorization for privileged operations.
- No arbitrary Panther URL / SSRF parameter.
- No privileged CRM data stored only in localStorage.
