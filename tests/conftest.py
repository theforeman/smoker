import pytest
import requests
import apypie
import time

from collections import namedtuple

User = namedtuple('User', ['username', 'password', 'name'])

PAGES = [
    '/',
    '/architectures',
    '/hosts',
    '/models',
    '/media',
    '/operatingsystems',
    '/templates/ptables',
    '/templates/provisioning_templates',
    '/hostgroups',
    '/common_parameters',
    '/environments',
    '/puppetclasses',
    '/config_groups',
    '/variable_lookup_keys',
    '/puppetclass_lookup_keys',
    '/smart_proxies',
    '/compute_resources',
    '/compute_profiles',
    '/subnets',
    '/domains',
    '/http_proxies',
    '/realms',
    '/locations',
    '/organizations',
    '/auth_source_ldaps',
    '/users',
    '/usergroups',
    '/roles',
    '/bookmarks',
    '/settings',
    '/about',
]


def pytest_generate_tests(metafunc):
    if 'url' in metafunc.fixturenames:
        base_url = metafunc.config.option.base_url
        assert base_url

        # mimic the variables fixture from pytest-variables
        user_obj = _user(metafunc.config._variables)  # pylint: disable=protected-access

        response = requests.get(f'{base_url}/menu', auth=(user_obj.username, user_obj.password),
                                verify=False)
        if response.status_code == 404:
            # Menu is only available since Foreman 2.0
            pages = [base_url + page for page in PAGES]
        else:
            assert response
            pages = [pytest.param(base_url + page['url'], id=page['name'])
                     for page in response.json()
                     # logout has an error "Cannot read property 'icon' of null"
                     if page['url'] != '/users/logout']

        metafunc.parametrize('url', pages)


def _user(variables):
    return User(variables.get('username', 'admin'), variables.get('password', 'changeme'),
                variables.get('name', 'Admin User'))


@pytest.fixture(scope='session')
def user(variables):
    return _user(variables)


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


def wait_for_task(task, api):
    duration = 60
    poll = 15

    while task['state'] not in ['paused', 'stopped']:
        duration -= poll
        if duration <= 0:
            break
        time.sleep(poll)

        task = api.resource('foreman_tasks').call('show', {'id': task['id']})

    return task
