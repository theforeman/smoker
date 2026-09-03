import time
import warnings

PING_POLL_INTERVAL = 5
PING_POLL_TIMEOUT = 60


def _assert_ping(ping):
    assert ping['foreman']['database']['active']

    for subsystem, data in ping.items():
        try:
            assert data['status'] == 'ok', f"{subsystem} is ok"
        except KeyError:
            warnings.warn("Foreman doesn't have a status - issue https://projects.theforeman.org/issues/31545")


def test_ping(api):
    deadline = time.monotonic() + PING_POLL_TIMEOUT
    while time.monotonic() < deadline:
        ping = api.resource('ping').call('ping')['results']
        try:
            _assert_ping(ping)
            return
        except AssertionError:
            time.sleep(PING_POLL_INTERVAL)

    _assert_ping(api.resource('ping').call('ping')['results'])
