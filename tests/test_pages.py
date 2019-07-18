# pylint: disable=redefined-outer-name
from __future__ import print_function

from collections import namedtuple

import pytest

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

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


@pytest.fixture
def firefox_options(firefox_options):
    firefox_options.headless = True
    return firefox_options


@pytest.fixture
def chrome_options(chrome_options):
    chrome_options.headless = True
    # The error log is a non-w3c option
    chrome_options.add_experimental_option('w3c', False)
    return chrome_options


@pytest.fixture
def user(variables):
    return User(variables.get('username', 'admin'), variables.get('password', 'changeme'),
                variables.get('name', 'Admin User'))


@pytest.fixture(params=PAGES)
def url(request, base_url):
    if not base_url:
        raise ValueError('Base URL not specified')
    return base_url + request.param


@pytest.mark.nondestructive
@pytest.mark.selenium
def test_page(selenium, user, url):
    selenium.get(url)
    assert selenium.current_url.endswith('/users/login')
    login_field = selenium.find_element_by_name('login[login]')
    login_field.send_keys(user.username)
    password_field = selenium.find_element_by_name('login[password]')
    password_field.send_keys(user.password)
    password_field.submit()

    account_menu = WebDriverWait(selenium, 10).until(
        EC.presence_of_element_located((By.ID, 'account_menu'))
    )
    assert account_menu.text == user.name
    assert selenium.current_url == url

    if selenium.name == 'firefox':
        print("Firefox hasn't implemented webdriver logging")
        print("https://github.com/mozilla/geckodriver/issues/284")

    logs = selenium.get_log('browser')
    assert not [x['message'] for x in logs if x.get('level') == 'SEVERE']
