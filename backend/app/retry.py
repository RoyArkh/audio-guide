"""POST with retries. Rate limits (429) and overloaded servers (5xx) usually clear up after a short wait."""

import logging
import time

import httpx2

log = logging.getLogger(__name__)

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
RETRY_DELAYS_S = [2, 8, 30]


def post_with_retries(client: httpx2.Client, url: str, body: dict) -> httpx2.Response:
    """Returns the last response, which may still be an error. Network errors raise httpx2.HTTPError."""
    for delay_s in RETRY_DELAYS_S:
        response = client.post(url, json=body)
        if response.status_code not in RETRYABLE_STATUS_CODES:
            return response
        log.warning("%s returned %d, retrying in %d s", url, response.status_code, delay_s)
        time.sleep(delay_s)
    return client.post(url, json=body)
