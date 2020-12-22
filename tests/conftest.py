import pytest

from collections import namedtuple

User = namedtuple('User', ['username', 'password', 'name'])


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
