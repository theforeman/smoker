import apypie
import pytest
import requests

from collections import namedtuple
from urllib.parse import urlparse

User = namedtuple('User', ['username', 'password', 'name'])


def pytest_generate_tests(metafunc):
    variables = metafunc.config._variables  # pylint: disable=protected-access

    if 'url' in metafunc.fixturenames:
        base_url = metafunc.config.option.base_url
        assert base_url

        # mimic the variables fixture from pytest-variables
        user_obj = _user(metafunc.config._variables)  # pylint: disable=protected-access

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


@pytest.fixture(scope='session')
def api(user, base_url):
    return apypie.Api(
        uri=base_url,
        username=user.username,
        password=user.password,
        api_version=2,
        verify_ssl=False,
    )


@pytest.fixture(scope='session')
def registration_hostname(base_url):
    return urlparse(base_url).hostname
