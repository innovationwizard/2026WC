#!/usr/bin/env python3
"""
af_client.py — cached API-Football client (M3 build, Batch B1.1).

A thin, dependency-free wrapper around the API-Football v3 REST API that:
  - reads the key from the repo .env (var name is `API-KEY`, note the hyphen),
  - caches every response to disk under v2/m3/cache/ so a given call is fetched
    ONCE and re-runs cost zero API calls (Dirty George: raw JSON is the auditable
    record; parsing happens later off the cache),
  - tracks how many live API calls this process has made,
  - surfaces the daily quota (from API-Football's rate-limit headers) and warns
    as it runs low against the Pro plan's 7,500/day.

Raw cache is gitignored: caching is permitted by the API terms, but redistributing
raw API data is not, and this repo is public.

  python v2/m3/af_client.py        # self-test: /status twice (live then cached)
"""
import os
import re
import json
import time
import urllib.request
import urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
ENV = os.path.join(ROOT, '.env')
CACHE_DIR = os.path.join(HERE, 'cache')

HOST = 'https://v3.football.api-sports.io'
DAILY_LIMIT_HINT = 7500          # Pro plan; real value comes from response headers
LOW_QUOTA_WARN = 500             # warn when fewer than this remain today

# ---- module state (this process only) ----
_LIVE_CALLS = 0                  # live HTTP calls made (cache hits excluded)
_LAST_QUOTA = {'limit': None, 'remaining': None}


def load_api_key():
    """Resolve the API-Football key.

    Order: environment first (so headless/CI runs — where the repo .env is
    gitignored and absent — can inject it as a secret), then the .env file. The
    canonical var name has a hyphen, which isn't a valid shell identifier, so the
    underscore form is also accepted for the environment path."""
    for var in ('API-KEY', 'API_KEY', 'APISPORTS_KEY'):
        v = os.environ.get(var)
        if v and v.strip():
            return v.strip().strip('"').strip("'")
    if not os.path.exists(ENV):
        raise SystemExit(f'.env not found at {ENV} and no API key in environment')
    with open(ENV) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if line.split('=', 1)[0].strip() == 'API-KEY':
                return line.split('=', 1)[1].strip().strip('"').strip("'")
    raise SystemExit('API-KEY not found in .env')


def _cache_path(path):
    """Map an API path like '/fixtures?league=1&season=2022' to a readable,
    filesystem-safe cache filename."""
    name = path.lstrip('/')
    name = re.sub(r'[?&]', '__', name)
    name = re.sub(r'[^A-Za-z0-9=_.\-]', '_', name)
    return os.path.join(CACHE_DIR, name + '.json')


def live_calls():
    return _LIVE_CALLS


def last_quota():
    return dict(_LAST_QUOTA)


def get(path, force=False, pause=0.0):
    """GET an API path, returning the parsed JSON. Served from disk cache unless
    `force=True`. `pause` sleeps before a LIVE call (politeness/rate-limit); it is
    skipped on cache hits.

    On an API error the error payload is returned (with an '_http_error' key) but
    is NOT cached, so a transient failure can be retried on the next run.
    """
    global _LIVE_CALLS
    os.makedirs(CACHE_DIR, exist_ok=True)
    cp = _cache_path(path)

    if not force and os.path.exists(cp):
        with open(cp) as f:
            return json.load(f)

    if pause:
        time.sleep(pause)

    key = load_api_key()
    req = urllib.request.Request(HOST + path, headers={'x-apisports-key': key})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
            _record_quota(r.headers)
    except urllib.error.HTTPError as e:
        return {'_http_error': e.code, '_body': e.read().decode()[:500], '_path': path}
    except urllib.error.URLError as e:
        return {'_url_error': str(e.reason), '_path': path}

    _LIVE_CALLS += 1

    # API-Football returns HTTP 200 with an "errors" object on quota/plan problems;
    # surface those but do not cache a non-result.
    if isinstance(data, dict) and data.get('errors'):
        data['_api_errors'] = data['errors']
        return data

    with open(cp, 'w') as f:
        json.dump(data, f)
    return data


def _record_quota(headers):
    global _LAST_QUOTA
    try:
        lim = headers.get('x-ratelimit-requests-limit')
        rem = headers.get('x-ratelimit-requests-remaining')
        _LAST_QUOTA = {
            'limit': int(lim) if lim is not None else None,
            'remaining': int(rem) if rem is not None else None,
        }
        if _LAST_QUOTA['remaining'] is not None and _LAST_QUOTA['remaining'] < LOW_QUOTA_WARN:
            print(f"  [af_client] WARNING: only {_LAST_QUOTA['remaining']} API calls "
                  f"left today (limit {_LAST_QUOTA['limit']}).")
    except (TypeError, ValueError):
        pass


def _selftest():
    print('B1.1 self-test — /status live then cached')
    cp = _cache_path('/status')
    if os.path.exists(cp):
        os.remove(cp)  # force a clean live fetch for the test

    d1 = get('/status')
    sub = (d1.get('response') or {}).get('subscription', {})
    print(f"  live call 1: plan={sub.get('plan')} active={sub.get('active')} "
          f"| live_calls={live_calls()} | quota={last_quota()}")
    assert live_calls() == 1, 'expected exactly 1 live call'
    assert os.path.exists(cp), 'expected /status to be cached after live call'

    d2 = get('/status')
    print(f"  call 2 (cache hit): live_calls still {live_calls()}")
    assert live_calls() == 1, 'cache hit must NOT make a live call'
    assert d2 == d1, 'cached payload should equal the live payload'

    print('  PASS — caching works, counter excludes cache hits.')


if __name__ == '__main__':
    _selftest()
