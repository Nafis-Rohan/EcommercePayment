# Environment Configuration & ngrok Setup Guide

## 1. Environment variables

Copy `.env.example` to `.env` and fill in real values:

```bash
cp .env.example .env
```

| Variable | Purpose |
|---|---|
| `DEBUG` | `True` for local dev, `False` in production |
| `SECRET_KEY` | Django's cryptographic signing key — generate a real random one, never reuse the example |
| `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` | Database credentials, matched to `docker-compose.yml` |
| `POSTGRES_HOST` / `POSTGRES_PORT` | `localhost:5433` when running `manage.py runserver` directly on your machine; the `backend` service in `docker-compose.yml` overrides these to `db:5432` automatically for in-container use |
| `REDIS_URL` | Same idea — `redis://localhost:6379/1` for local runserver, overridden to `redis://redis:6379/1` inside Docker |
| `CORS_ALLOWED_ORIGINS` | Comma-separated list of origins allowed to call this API — your local frontend dev server, and your deployed Vercel URL |
| `STRIPE_SECRET_KEY` | From Stripe Dashboard → Developers → API keys (`sk_test_...` for test mode) |
| `STRIPE_WEBHOOK_SECRET` | From your Stripe webhook destination's signing secret (`whsec_...`) |
| `BKASH_APP_KEY` / `BKASH_APP_SECRET` / `BKASH_USERNAME` / `BKASH_PASSWORD` | From bKash's sandbox developer portal |
| `BKASH_BASE_URL` | Must be the **API** domain — `https://tokenized.sandbox.bka.sh/v1.2.0-beta` — not the customer-facing checkout domain |

**Important**: environment variables are only read once, when the process starts.
Editing `.env` while the backend is already running has no effect until it's
restarted — and for the Dockerized `backend` service specifically, a plain
`docker-compose restart backend` is **not enough**, because that only restarts the
process inside the same container, whose environment was already baked in at
creation time via `env_file`. Any `.env` change needs:

```bash
docker-compose up -d --force-recreate backend
```

Verify it actually took effect:

```bash
docker exec ecommerce_backend python manage.py shell -c "from django.conf import settings; print(settings.CORS_ALLOWED_ORIGINS)"
```

## 2. Exposing the backend publicly with ngrok

Both Stripe's webhook and the deployed Vercel frontend need a real, public URL to
reach a backend that only runs on `localhost`. [ngrok](https://ngrok.com) tunnels a
local port to a public HTTPS address.

**One-time setup:**
1. Sign up at ngrok.com and copy your authtoken from the dashboard (Settings → Your Authtoken).
2. Configure it locally (replace the placeholder — never commit a real authtoken anywhere public):
   ```bash
   ngrok config add-authtoken <your-authtoken>
   ```

**Every time you want the backend reachable:**
```bash
ngrok http 8000
```

This prints a line like:
```
Forwarding    https://detonator-folk-claw.ngrok-free.dev -> http://localhost:8000
```

That `https://...ngrok-free.dev` address is now a real, internet-reachable URL for
your local backend. Two places need updating whenever it changes:

1. **Stripe webhook destination** — set its endpoint URL to
   `https://<your-ngrok-url>/api/payments/webhook/stripe/`.
2. **Frontend config** — `frontend/js/config.js`'s `API_BASE_URL` needs to match this
   same URL + `/api`, then redeploy (push to `main`, Vercel auto-redeploys).

**Free-tier ngrok assigns a new random URL every time you restart it** — both of the
above need updating each time that happens, unless you're on a paid plan with a
reserved domain.

**One extra gotcha specific to this project**: ngrok's free tier shows a
browser-warning interstitial page (plain text, not JSON) to any request that looks
like it's coming from a browser. This backend's CORS config explicitly allows a
custom `ngrok-skip-browser-warning` header (see `CORS_ALLOW_HEADERS` in
`config/settings.py`) so the frontend can bypass it — if you fork this project and
requests to your own ngrok URL start returning HTML instead of JSON, this is why, and
the frontend's `fetch` calls already send that header for you.

## 3. Quick local run checklist

```bash
docker-compose up -d                                   # Postgres + Redis + backend
docker exec ecommerce_backend python manage.py migrate
docker exec ecommerce_backend python manage.py seed_admin
docker exec ecommerce_backend python manage.py seed_products
ngrok http 8000                                          # if you need a public URL
```
