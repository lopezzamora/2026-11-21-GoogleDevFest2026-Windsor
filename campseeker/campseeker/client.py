"""Read-only NPS client. Transport injection permits genuinely offline tests."""
from datetime import datetime, timezone
import re
from urllib.parse import urlencode

BASE_URL = 'https://developer.nps.gov/api/v1/'
RESOURCES = {'parks', 'campgrounds', 'alerts'}
STATE_CODES = set(('AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD '
                   'MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC '
                   'SD TN TX UT VT VA WA WV WI WY DC AS GU MP PR VI').split())


class NPSFailure(Exception):
    """Safe error details only; never include request headers or response bodies."""
    def __init__(self, code, message, retry_after=None):
        super().__init__(message)
        self.code, self.retry_after = code, retry_after


def requests_transport(resource, params, api_key, timeout):
    """Use requests only against the fixed NPS host, never model-provided URLs."""
    try:
        import requests
    except ImportError:
        raise NPSFailure('missing_dependency', 'Install the project requirements first.') from None
    try:
        response = requests.get(
            BASE_URL + resource,
            params=params,
            headers={'X-Api-Key': api_key, 'User-Agent': 'DevFest-NPS-Camping-Demo/0.1'},
            timeout=(3.05, timeout),
            allow_redirects=False,  # Do not forward credentials to redirected hosts.
        )
    except requests.Timeout:
        raise NPSFailure('timeout', 'The NPS request timed out; conditions remain unverified.') from None
    except requests.RequestException:
        raise NPSFailure('network_error', 'The NPS service could not be reached.') from None
    if response.status_code in (401, 403):
        raise NPSFailure('authentication_error', 'NPS rejected the API key; check configuration.')
    if response.status_code == 429:
        retry = response.headers.get('Retry-After', '')
        retry = int(retry) if str(retry).isdigit() else None
        raise NPSFailure('rate_limited', 'NPS rate limit reached; retry later.', retry)
    if response.status_code != 200:
        raise NPSFailure('http_error', f'NPS returned HTTP {response.status_code}.')
    try:
        return response.json()
    except ValueError:
        raise NPSFailure('invalid_response', 'NPS returned invalid JSON.') from None


class NPSClient:
    def __init__(self, api_key, timeout=15.0, transport=None):
        self._api_key = api_key
        self.timeout = timeout
        self.transport = transport or requests_transport

    def query(self, resource, *, query='', state_code='', park_code='', limit=20, start=0):
        """Return one explicit page; missing data must never become a false negative."""
        try:
            if resource not in RESOURCES:
                raise ValueError('Unsupported NPS resource.')
            if type(limit) is not int or not 1 <= limit <= 50:
                raise ValueError('limit must be an integer between 1 and 50.')
            if type(start) is not int or start < 0:
                raise ValueError('start must be a non-negative integer.')
            if not all(isinstance(v, str) for v in (query, state_code, park_code)):
                raise ValueError('Search values must be strings.')
            if len(query) > 200:
                raise ValueError('query must contain at most 200 characters.')
            state_code, park_code = state_code.strip().upper(), park_code.strip().lower()
            if state_code and state_code not in STATE_CODES:
                raise ValueError('state_code must be one US postal code, such as ME or VA.')
            if park_code and not re.fullmatch(r'[a-z0-9]{4}', park_code):
                raise ValueError('park_code must be a four-character code returned by search_parks.')
            if resource != 'parks' and not park_code:
                raise ValueError('A park_code is required for campground and alert lookups.')
            params = {'limit': limit, 'start': start}
            if query.strip():
                params['q'] = query.strip()
            if state_code:
                params['stateCode'] = state_code
            if park_code:
                params['parkCode'] = park_code
            payload = self.transport(resource, params, self._api_key, self.timeout)
            if not isinstance(payload, dict) or not isinstance(payload.get('data'), list):
                raise NPSFailure('invalid_response', 'NPS response has no valid data list.')
            records = payload['data']
            if any(not isinstance(item, dict) for item in records):
                raise NPSFailure('invalid_response', 'NPS response contains invalid records.')
            raw_total = payload.get('total')
            if isinstance(raw_total, bool) or not str(raw_total).isdigit():
                raise NPSFailure('invalid_response', 'NPS response has no valid total count.')
            total = int(raw_total)
            if total < len(records) or len(records) > limit:
                raise NPSFailure('invalid_response', 'NPS response counts are inconsistent.')
            has_more = start + len(records) < total
            if has_more and not records:
                raise NPSFailure('invalid_response', 'NPS returned an empty page before the end.')
            return {
                'status': 'success', 'resource': resource,
                'source': 'NPS API',
                'source_url': BASE_URL + resource + '?' + urlencode(params),
                'retrieved_at_utc': datetime.now(timezone.utc).isoformat(),
                'start': start, 'count': len(records), 'total': total,
                'has_more': has_more, 'next_start': start + len(records) if has_more else None,
                'coverage': 'partial_page' if start > 0 or has_more else 'complete_query_result',
                'data': records,
            }
        except ValueError as exc:
            return {'status': 'error', 'error_code': 'invalid_input', 'message': str(exc)}
        except NPSFailure as exc:
            result = {'status': 'error', 'error_code': exc.code, 'message': str(exc)}
            if exc.retry_after is not None:
                result['retry_after_seconds'] = exc.retry_after
            return result
