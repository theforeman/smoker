import apypie
import py.path
import pytest
import requests
import uuid

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


@pytest.fixture(scope="module")
def fixture_dir():
    return py.path.local(__file__).realpath() / '..' / 'fixtures'


@pytest.fixture
def organization(api):
    org = api.create('organizations', {'name': str(uuid.uuid4())})
    yield org
    api.delete('organizations', org)


@pytest.fixture
def product(organization, api):
    prod = api.create('products', {'name': str(uuid.uuid4()), 'organization_id': organization['id']})
    yield prod
    api.delete('products', prod)


@pytest.fixture
def yum_repository(product, organization, api):
    repo = api.create('repositories', {'name': str(uuid.uuid4()), 'product_id': product['id'], 'content_type': 'yum', 'url': 'https://fixtures.pulpproject.org/rpm-no-comps/'})
    wait_for_metadata_generate(api)
    yield repo
    api.delete('repositories', repo)


@pytest.fixture
def file_repository(product, organization, api):
    repo = api.create('repositories', {'name': str(uuid.uuid4()), 'product_id': product['id'], 'content_type': 'file', 'url': 'https://fixtures.pulpproject.org/file/'})
    wait_for_metadata_generate(api)
    yield repo
    api.delete('repositories', repo)


@pytest.fixture
def container_repository(product, organization, api):
    parameters = {
        'name': str(uuid.uuid4()),
        'product_id': product['id'],
        'content_type': 'docker',
        'url': 'https://quay.io/',
        'docker_upstream_name': 'foreman/busybox-test',
    }
    repo = api.create('repositories', parameters)
    wait_for_metadata_generate(api)
    yield repo
    api.delete('repositories', repo)


@pytest.fixture
def lifecycle_environment(organization, api):
    library = api.list('lifecycle_environments', 'name=Library', {'organization_id': organization['id']})[0]
    lce = api.create('lifecycle_environments', {'name': str(uuid.uuid4()), 'organization_id': organization['id'], 'prior_id': library['id']})
    yield lce
    api.delete('lifecycle_environments', lce)


@pytest.fixture
def content_view(organization, api):
    cv = api.create('content_views', {'name': str(uuid.uuid4()), 'organization_id': organization['id']})
    yield cv
    api.delete('content_views', cv)


def wait_for_tasks(api, search=None):
    tasks = api.list('foreman_tasks', search=search)
    for task in tasks:
        api.wait_for_task(task)


def wait_for_metadata_generate(api):
    wait_for_tasks(api, 'label = Actions::Katello::Repository::MetadataGenerate')
