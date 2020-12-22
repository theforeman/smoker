import warnings


def test_ping(api):
    ping = api.resource('ping').call('ping')['results']

    assert ping['foreman']['database']['active']

    for subsystem, data in ping.items():
        try:
            assert data['status'] == 'ok', f"{subsystem} is ok"
        except KeyError:
            warnings.warn("Foreman doesn't have a status - issue https://projects.theforeman.org/issues/31545")
