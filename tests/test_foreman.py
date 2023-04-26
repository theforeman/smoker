import pytest

from urllib.parse import urlparse


def test_foreman_version(api, variables):
    try:
        expected_foreman_version = variables['expected_foreman_version']
    except KeyError:
        pytest.skip("'expected_foreman_version' is not set")
    else:
        status = api.resource('home').call('status')
        assert status['version'] == expected_foreman_version


def test_ping(api):
    ping = api.resource('ping').call('ping')['results']

    assert ping['foreman']['database']['active']

    try:
        assert ping['katello']['status'] == 'ok'
    except KeyError:
        pytest.skip("'katello plugin' is not present")


def test_check_smart_proxy_registered(api, base_url):
    hostname = urlparse(base_url).hostname
    assert api.resource('smart_proxies').call('show', {'id': hostname})
