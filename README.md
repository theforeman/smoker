# Smoker - Smoke testing the Foreman and friends

Smoker is a [smoke testing](https://en.wikipedia.org/wiki/Smoke_testing_%28software%29) tool aimed at verifying [Foreman](https://theforeman.org/)'s functionality and testing for regressions. Testing plug-ins is also within scope, but it should be optional.

It's written in Python 3 and heavily relies on [pytest](https://pytest.org). To ensure it doesn't rely on anything on the system under test the ideal deployment is on a separate machine.
