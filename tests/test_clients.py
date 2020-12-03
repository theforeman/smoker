import pytest
import testinfra


def pytest_generate_tests(metafunc):
    if 'linux_client' in metafunc.fixturenames:
        host = testinfra.get_host('local://')
        containers = host.podman.get_containers(label='smoker-linux-client', status='running')
        linux_clients = [f"podman://{container.id}" for container in containers]
        ids = [container.name for container in containers]

        metafunc.parametrize('linux_client', linux_clients, ids=ids, indirect=True)


@pytest.fixture(scope="module")
def linux_client(request):
    host = testinfra.get_host(request.param)

    subman = host.package("subscription-manager")
    if not subman.is_installed:
        print('Installing subscription-manager')
        host.run('yum -y install subscription-manager')

    return host


def test_subman_installed(linux_client):
    subman = linux_client.package("subscription-manager")
    assert subman.is_installed
