# Smoker - Smoke testing the Foreman and friends

Smoker is a [smoke testing](https://en.wikipedia.org/wiki/Smoke_testing_%28software%29) tool aimed at verifying [Foreman](https://theforeman.org/)'s functionality and testing for regressions. Testing plug-ins is also within scope, but it should be optional.

It's written in Python 3 and heavily relies on [pytest](https://pytest.org). To ensure it doesn't rely on anything on the system under test the ideal deployment is on a separate machine.

# Running tests

First install the dependencies:

```sh
pip install -r requirements.txt
```

To run, a base URL needs to be passed in:

```
pytest --base-url https://foreman.example.com
```

## Variables

It is possible to specify the username, password and admin name via variables:

```json
{
  "username": "admin",
  "password": "changeme",
  "name": "Admin User"
}
```

This can be passed in on the command line:

```
pytest --variables variables.json
```

## Selenium

To specify the correct driver for Selenium, the `--driver` parameters is used.

```
pytest --driver Chrome
```

This will also need Chrome/Chromium along with the chromedriver. On Fedora:

```
dnf install chromedriver chromium
```

Note that Firefox isn't fully supported because it [doesn't implement the webdriver logging](https://github.com/mozilla/geckodriver/issues/284). [geckodriver](https://github.com/mozilla/geckodriver) isn't packaged either.

## Markers

Every test can be annotated by [pytest markers](https://docs.pytest.org/en/latest/mark.html). They are commonly used to select tests.

To only run Selenium tests:

```
pytest -m selenium
```

They can also be used to skip Selenium tests:

```
pytest -m 'not selenium'
```

To see all markers:

```
pytest --markers
```

## Client Tests

The client tests require the input set of containers to exist prior to running. All the required images can be built based on the version of Foreman being tested:

```
./build_images.sh <version>
```

The set of clients to test must also be specified in `variables.json`:

```
  "clients": [
    "smoker-test/centos8:nightly",
    "smoker-test/centos7:nightly"
  ]
```

By default, the client tests support testing the EL7 and EL8 images due to the complexities of rootless containers with systemd.

### EL6 Client Tests

The EL6 client container based tests can be ran when using an EL7 host due to the complexities of running rootless containers with podman and systemd. To test this manully, assuming you have spun up an EL7 machine with podman present and smoker checked out, build the images:

```
./build_images.sh nightly
```

Now update the variables.json to include only the EL6 container:

```
  "clients": [
    "smoker-test/centos6:nightly"
  ]
```

Additionally, due to how logging is handled, inside `tests/test_content_client.py`, you'll need to update the podman run command:

```
    container_id = subprocess.check_output([
        'podman',
        'run',
        '--systemd',
        'always',
        '--volume',
        '/dev/log:/dev/log',
        '--detach',
        '--tty',
        request.param
    ]).decode().strip()
```
