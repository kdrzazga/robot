# Customer DB — Application Under Test

A small FastAPI REST service backed by an in-memory SQLite database, built
to be exercised by Robot Framework test suites.

## Data model

- **address**: id, street, city, zip_code, country
- **person**: id, name, last_name, address_id (FK -> address.id)

## Authentication

OAuth2 password flow with JWT bearer tokens. Two fixed users:

| username | password | role  | access             |
|----------|----------|-------|--------------------|
| admin    | admin    | admin | full (GET/POST/PUT/DELETE) |
| user     | user     | user  | read-only (GET only)       |

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

```bash
python run.py
```

Server starts at http://127.0.0.1:8000 . Interactive docs (with a built-in
"Authorize" button for the bearer token) at http://127.0.0.1:8000/docs .

## Endpoints

- `POST /token` — login, get a JWT
- `POST /reset` — wipe and re-seed the DB to a known state (admin only;
  use this from a test suite's Suite Setup for a repeatable starting point)
- `GET/POST /addresses`, `GET/PUT/DELETE /addresses/{id}`
- `GET/POST /persons`, `GET/PUT/DELETE /persons/{id}` (person responses on
  GET include the full nested address, not just the address_id)

The database resets to the seeded dataset every time the app restarts, and
on demand via `POST /reset`.

## Note

The secret key and the two hardcoded users are for test purposes only —
this app is intentionally not production-hardened.
