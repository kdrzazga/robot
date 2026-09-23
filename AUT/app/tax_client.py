"""
Client for the TaxInformation service, used by the customer DB service.

The customer DB is the only component that talks to the tax service: the
browser UI goes through the customer DB's /taxes endpoints, which call the
functions below. Every call forwards the caller's bearer token, so the tax
service applies the same user/admin rules.

The base URL comes from the TAX_SERVICE_URL environment variable, so tests
can point the customer DB at a stub instead of the real tax service. It is
read once, when the service starts.

Uses only the standard library (urllib) so no extra dependency is needed.
"""
import json
import os
import urllib.error
import urllib.parse
import urllib.request

from fastapi import HTTPException

TAX_SERVICE_URL = os.environ.get("TAX_SERVICE_URL", "http://127.0.0.1:8001")
TIMEOUT_SECONDS = 5


def _call_tax_service(method: str, path: str, bearer_token: str, body: dict | None = None):
    """Sends one request to the tax service and returns its parsed JSON.

    Client errors (4xx, e.g. a duplicate tax_id or a 403 for non-admins) are
    passed through with the tax service's own status and detail; anything
    else becomes a 502 so it's clear the problem is downstream."""
    headers = {"Authorization": f"Bearer {bearer_token}"}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(TAX_SERVICE_URL + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as error:
        if 400 <= error.code < 500:
            raise HTTPException(status_code=error.code, detail=_error_detail(error))
        raise HTTPException(status_code=502, detail=f"Tax service returned HTTP {error.code}")
    except (urllib.error.URLError, TimeoutError):
        raise HTTPException(status_code=502, detail=f"Tax service unavailable at {TAX_SERVICE_URL}")
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="Tax service returned a non-JSON response")


def _error_detail(error: urllib.error.HTTPError):
    try:
        return json.loads(error.read()).get("detail", error.reason)
    except (json.JSONDecodeError, AttributeError):
        return error.reason


def list_tax_records(bearer_token: str, tax_id: str | None = None) -> list:
    query = f"?{urllib.parse.urlencode({'tax_id': tax_id})}" if tax_id is not None else ""
    return _call_tax_service("GET", f"/taxes{query}", bearer_token)


def fetch_tax_record(tax_id: str, bearer_token: str) -> dict:
    """Returns the tax service's record for `tax_id`, or 404 if it has none."""
    records = list_tax_records(bearer_token, tax_id)
    if not records:
        raise HTTPException(status_code=404, detail=f"No tax record for tax_id {tax_id}")
    return records[0]


def update_tax_record(record_id: int, record: dict, bearer_token: str) -> dict:
    return _call_tax_service("PUT", f"/taxes/{record_id}", bearer_token, record)
