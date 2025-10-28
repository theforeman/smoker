import apypie
import pytest
import requests

from functools import cached_property
from pytest_variables.plugin import variables_key
from collections import namedtuple
from urllib.parse import urlparse

User = namedtuple('User', ['username', 'password', 'name'])


class ForemanPlugins:
    def __init__(self, config):
        self._config = config

    @cached_property
    def plugins(self):
        client = _api(_user(self._config.stash[variables_key]), self._config.option.base_url)
        return {plugin['id'] for plugin in client.list('plugins')}


def pytest_configure(config):
    config.addinivalue_line('markers', 'internal: mark test as a self test')
    config.addinivalue_line('markers', 'plugin(name): mark test as a requiring a plugin')

    config.foreman_plugins = ForemanPlugins(config)


def pytest_runtest_setup(item):
    plugin_markers = set(mark.args[0] for mark in item.iter_markers(name="plugin"))
    if plugin_markers:
        missing = plugin_markers - item.config.foreman_plugins.plugins
        if missing:
            pytest.skip("test requires plugin(s) {!r}".format(missing))


def pytest_generate_tests(metafunc):
    variables = metafunc.config.stash[variables_key]

    if 'url' in metafunc.fixturenames:
        base_url = metafunc.config.option.base_url
        assert base_url

        user_obj = _user(variables)

        response = requests.get(f'{base_url}/menu', auth=(user_obj.username, user_obj.password),
                                verify=False)
        assert response
        pages = [pytest.param(base_url + page['url'], id=page['name'])
                 for page in response.json()
                 # logout has an error "Cannot read property 'icon' of null"
                 if page['url'] != '/users/logout']

        metafunc.parametrize('url', pages)

    if 'katello_client' in metafunc.fixturenames:
        clients = variables.get('clients', [])

        metafunc.parametrize('katello_client', clients, indirect=True)


def _user(variables):
    return User(variables.get('username', 'admin'), variables.get('password', 'changeme'),
                variables.get('name', 'Admin User'))


@pytest.fixture(scope='session')
def user(variables):
    return _user(variables)


@pytest.fixture(scope='session')
def entities():
    return {
        'organization_label': 'Test_Organization',
        'activation_key': 'Test AK',
        'product': 'Test Product',
        'product_label': 'Test_Product',
        'yum_repository': 'Zoo',
        'yum_repository_label': 'Zoo',
        'errata_id': 'RHEA-2012:0055',
        'container_repository_label': 'foremanbusybox'
    }


def _api(user, base_url):
    return apypie.ForemanApi(
        uri=base_url,
        username=user.username,
        password=user.password,
        api_version=2,
        verify_ssl=False,
    )


@pytest.fixture(scope='session')
def api(user, base_url):
    return _api(user, base_url)


@pytest.fixture(scope='session')
def registration_hostname(base_url):
    return urlparse(base_url).hostname
