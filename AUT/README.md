# Customer DB + TaxInformation — Application Under Test

Two small FastAPI REST services, each backed by its own in-memory SQLite
database, built to be exercised by Robot Framework test suites:

| service        | package    | run with          | URL                    |
|----------------|------------|-------------------|------------------------|
| Customer DB    | `app/`     | `python run.py`     | http://127.0.0.1:8000 |
| TaxInformation | `tax_app/` | `python run_tax.py` | http://127.0.0.1:8001 |

## Data model

- **address**: id, street, city, zip_code, country
- **person**: id, name, last_name, TAX_ID, address_id (FK -> address.id)
- **taxes** (TaxInformation service): id, name, last_name, TAX_ID, tax_amount

TAX_ID is unique in each table and links a person to their tax record
(JSON field name: `tax_id`). There is no enforced link between the two
services: the seed data matches TAX-1001..1003 on both sides, and TAX-1004
exists only in TaxInformation.

## Authentication

OAuth2 password flow with JWT bearer tokens. Two fixed users:

| username | password | role  | access             |
|----------|----------|-------|--------------------|
| admin    | admin    | admin | full (GET/POST/PUT/DELETE) |
| user     | user     | user  | read-only (GET only)       |

Both services share the same users and signing key, so a token from either
service's `/token` works on both.

Get a token:

```
POST /token
Content-Type: application/x-www-form-urlencoded

username=admin&password=admin
```

Response: `{"access_token": "...", "token_type": "bearer"}`

Use it on subsequent calls: `Authorization: Bearer <access_token>`

## Setup

```bash
cd AUT
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/macOS
pip install -r requirements.txt
```

## Run

Start both services, each in its own terminal:

```bash
python run.py
python run_tax.py
```

Customer DB starts at http://127.0.0.1:8000 , TaxInformation at
http://127.0.0.1:8001 . Interactive docs (with a built-in "Authorize" button
for the bearer token) at http://127.0.0.1:8000/docs and
http://127.0.0.1:8001/docs .

Web UI (served by the Customer DB service, `/` redirects to it) at
http://127.0.0.1:8000/ui/ . The browser only talks to the Customer DB service;
the Taxes tab goes through its `/taxes` endpoints, which forward to
TaxInformation, so that tab needs `run_tax.py` (or a stub on port 8001). Opening `app/frontend/index.html` straight from disk
also works while the servers run.

## Endpoints

- `POST /token` — login, get a JWT
- `POST /reset` — wipe and re-seed the DB to a known state (admin only;
  use this from a test suite's Suite Setup for a repeatable starting point)
- `GET/POST /addresses`, `GET/PUT/DELETE /addresses/{id}`
- `GET/POST /persons`, `GET/PUT/DELETE /persons/{id}` (person responses on
  GET include the full nested address, not just the address_id)
- `GET /persons/{id}/tax` — looks up the person's TAX_ID in the TaxInformation
  service and returns its record (forwards the caller's token). The tax
  service URL comes from the `TAX_SERVICE_URL` environment variable (default
  http://127.0.0.1:8001), so tests can point it at a stub. Returns 502 if the
  tax service can't be reached.
- `GET /taxes`, `PUT /taxes/{id}` (admin) — pass-through to TaxInformation's
  endpoints of the same name, forwarding the caller's token. Its 4xx errors
  (e.g. duplicate tax_id, 422 validation) are returned unchanged.

TaxInformation (port 8001):

- `POST /token` — same login as above
- `POST /reset` — wipe and re-seed the tax DB (admin only)
- `GET/POST /taxes`, `GET/PUT/DELETE /taxes/{id}`;
  `GET /taxes?tax_id=TAX-1001` filters by TAX_ID

Each database resets to its seeded dataset every time its service restarts, and
on demand via `POST /reset`.

## Note

The secret key and the two hardcoded users are for test purposes only —
this app is intentionally not production-hardened.
