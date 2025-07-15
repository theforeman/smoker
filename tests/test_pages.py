# pylint: disable=redefined-outer-name
from __future__ import print_function

from enum import IntFlag
from typing import Union, KeysView, List
from urllib.parse import ParseResult, urlparse, parse_qs, urlencode

import pytest

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException


# https://github.com/SeleniumHQ/selenium/wiki/Logging
BrowserLogLevel = IntFlag('BrowserLogLevel', ['ALL', 'DEBUG', 'INFO', 'WARNING', 'SEVERE', 'OFF'])


EXCLUDE_ERRORS = (
    # Fixed in Foreman 3.7 - https://projects.theforeman.org/issues/36093
    'Scrollbar test exception: TypeError:',
    # New hosts page wants to load table_preferences, but those might not exist
    'table_preferences/hosts'
)


@pytest.fixture
def firefox_options(firefox_options):
    firefox_options.add_argument('--headless')
    return firefox_options


@pytest.fixture
def chrome_options(chrome_options):
    chrome_options.add_argument('--headless')
    return chrome_options


@pytest.fixture(scope='session')
def session_capabilities(session_capabilities):
    session_capabilities['acceptInsecureCerts'] = True
    return session_capabilities


@pytest.fixture
def selenium(selenium):
    selenium.set_window_size(1920, 1080)
    return selenium


def filtered_url_query(url: str, allowed_query_params: Union[List, KeysView]) -> ParseResult:
    parsed_url = urlparse(url)
    query = parse_qs(parsed_url.query)
    reduced_query = {key: value for key, value in query.items() if key in allowed_query_params}
    new_query = urlencode(reduced_query, doseq=True)
    return parsed_url._replace(query=new_query)


@pytest.mark.nondestructive
@pytest.mark.selenium
def test_menu_item(selenium, user, url, variables):
    selenium.get(url)
    assert selenium.current_url.endswith('/users/login'), 'Redirect to login page'
    login_field = selenium.find_element(By.NAME, 'login[login]')
    login_field.send_keys(user.username)
    password_field = selenium.find_element(By.NAME, 'login[password]')
    password_field.send_keys(user.password)
    password_field.submit()

    account_menu = WebDriverWait(selenium, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'user-nav-item'))
    )
    assert account_menu.text == user.name, 'Logged in user shows the correct name'

    expected_parsed_url = urlparse(url)
    allowed_query_params = parse_qs(expected_parsed_url.query).keys()
    actual_parsed_url = filtered_url_query(selenium.current_url, allowed_query_params)
    assert actual_parsed_url == expected_parsed_url, 'Correct page is loaded'

    if selenium.name == 'firefox':
        print("Firefox hasn't implemented webdriver logging")
        print("https://github.com/mozilla/geckodriver/issues/284")

    logs = selenium.get_log('browser')
    threshold = BrowserLogLevel[variables.get('browser_log_threshold', 'SEVERE')]
    messages = [x['message'] for x in logs
                if BrowserLogLevel[x['level']] >= threshold
                and not any(excl in x['message'] for excl in EXCLUDE_ERRORS)]
    assert messages == [], f'Messages with log level {threshold} or above in browser console'


@pytest.mark.parametrize('level,expected',
                         [
                             ('ALL', True),
                             ('SEVERE', True),
                             ('OFF', False),
                         ])
@pytest.mark.internal
def test_browser_log_level(level, expected):
    """
    Self test the logic to determine if browser log matches
    """
    assert (BrowserLogLevel.SEVERE >= BrowserLogLevel[level]) == expected
