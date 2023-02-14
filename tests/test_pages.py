# pylint: disable=redefined-outer-name
from __future__ import print_function

from typing import Union, KeysView, List
from urllib.parse import ParseResult, urlparse, parse_qs, urlencode

import pytest

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException


@pytest.fixture
def firefox_options(firefox_options):
    firefox_options.add_argument('--headless')
    return firefox_options


@pytest.fixture
def chrome_options(chrome_options):
    chrome_options.add_argument('--headless')
    # The error log is a non-w3c option
    chrome_options.add_experimental_option('w3c', False)
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
def test_menu_item(selenium, user, url):
    selenium.get(url)
    assert selenium.current_url.endswith('/users/login'), 'Redirect to login page'
    login_field = selenium.find_element(By.NAME, 'login[login]')
    login_field.send_keys(user.username)
    password_field = selenium.find_element(By.NAME, 'login[password]')
    password_field.send_keys(user.password)
    password_field.submit()

    # Foreman 2.5 changed the navigation
    try:
        account_menu = WebDriverWait(selenium, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'user-nav-item'))
        )
    except TimeoutException:
        account_menu = WebDriverWait(selenium, 10).until(
            EC.presence_of_element_located((By.ID, 'account_menu'))
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
    severe_messages = [x['message'] for x in logs if x.get('level') == 'SEVERE']
    assert severe_messages == [], 'Error messages with log level SEVERE in browser console'
