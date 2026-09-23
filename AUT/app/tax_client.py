"""
Client for the TaxInformation service, used by the customer DB service.

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


def fetch_tax_record(tax_id: str, bearer_token: str) -> dict:
    """Returns the tax service's record for `tax_id`, forwarding the caller's token."""
    url = f"{TAX_SERVICE_URL}/taxes?{urllib.parse.urlencode({'tax_id': tax_id})}"
    request = urllib.request.Request(url, headers={"Authorization": f"Bearer {bearer_token}"})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            records = json.loads(response.read())
    except urllib.error.HTTPError as error:
        raise HTTPException(status_code=502, detail=f"Tax service returned HTTP {error.code}")
    except (urllib.error.URLError, TimeoutError):
        raise HTTPException(status_code=502, detail=f"Tax service unavailable at {TAX_SERVICE_URL}")
    if not records:
        raise HTTPException(status_code=404, detail=f"No tax record for tax_id {tax_id}")
    return records[0]
