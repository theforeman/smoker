import pytest
import testinfra
import time
import subprocess


@pytest.fixture
def katello_client(request, entities, registration_hostname):
    image_id = subprocess.check_output(['podman', 'images', '-q', '--filter', f"reference={request.param}"])
    assert image_id

    container_id = subprocess.check_output([
        'podman',
        'run',
        '--volume',
        '/dev/log:/dev/log',
        '--detach',
        '--tty',
        request.param
    ]).decode().strip()

    try:
        container = testinfra.get_host("podman://" + container_id)

        container.run_expect([0], f"rpm -Uvh http://{registration_hostname}/pub/katello-ca-consumer-latest.noarch.rpm")
        container.run_expect([0], f"subscription-manager register --force --org={entities['organization_label']} --activationkey=\"{entities['activation_key']}\"")

        consumed = container.check_output("subscription-manager list --consumed")
        assert entities['product'] in consumed

        # return a testinfra connection to the container
        yield container

    finally:
        subprocess.check_call(['podman', 'rm', '-f', container_id])


@pytest.fixture
def katello_agent_client(katello_client):
    katello_client.run_expect([0], 'yum -y install katello-agent')

    katello_agent = katello_client.package('katello-agent')
    assert katello_agent.is_installed

    return katello_client


@pytest.fixture
def os_release_major(katello_client):
    return katello_client.system_info.release.split('.')[0]


def wait_for_task(task, api):
    duration = 60
    poll = 15

    while task['state'] not in ['paused', 'stopped']:
        duration -= poll
        if duration <= 0:
            break
        time.sleep(poll)

        task = api.resource('foreman_tasks').call('show', {'id': task['id']})


def foreman_host(client, api):
    hostname = client.check_output('hostname -s')
    return api.resource('hosts').call('show', {'id': hostname})


def test_register_with_subscription_manager(katello_client, entities, api, user):
    command = f"subscription-manager register --force --org={entities['organization_label']} --username={user.username} --password={user.password} --env=Library"
    katello_client.run_expect([0], command)

    assert foreman_host(katello_client, api)


def test_enable_content_view_repo(katello_client, entities):
    enable = katello_client.check_output(
        f"subscription-manager repos --enable={entities['organization_label']}_{entities['product_label']}_{entities['yum_repository_label']}"
    )

    assert "is enabled for this system" in enable


def test_install_katello_host_tools(katello_client):
    katello_client.run_expect([0], 'yum -y install katello-host-tools')
    katello_host_tools = katello_client.package('katello-host-tools')
    assert katello_host_tools.is_installed


def test_install_package_local(katello_client):
    katello_client.run('yum -y install walrus-0.71')
    walrus = katello_client.package('walrus')

    assert walrus.is_installed
    assert walrus.version == '0.71'


def test_available_errata(katello_client, entities, api, os_release_major):
    if os_release_major == "6":
        katello_client.run_expect([0], 'yum -y install katello-host-tools')

    katello_client.run('yum -y install walrus-0.71')

    host = foreman_host(katello_client, api)
    errata = api.resource('errata').call('index', {'host_id': host['id']})
    errata_ids = [erratum['errata_id'] for erratum in errata['results']]

    assert entities['errata_id'] in errata_ids


@pytest.mark.katello_agent
def test_katello_agent_package_install(katello_agent_client, api):
    host = foreman_host(katello_agent_client, api)
    task = api.resource('host_packages').call('install', {'host_id': host['id'], 'packages': ['gorilla']})
    wait_for_task(task, api)

    gorilla = katello_agent_client.package('gorilla')
    assert gorilla.is_installed


@pytest.mark.katello_agent
def test_katello_agent_errata_install(katello_agent_client, entities, api):
    katello_agent_client.run('yum -y install walrus-0.71')
    host = foreman_host(katello_agent_client, api)
    task = api.resource('host_errata').call('apply', {
        'host_id': host['id'],
        'errata_ids': [entities['errata_id']],
        'included': {},
        'excluded': {}
    })
    wait_for_task(task, api)

    walrus = katello_agent_client.package('walrus')
    assert walrus.is_installed
    assert walrus.version == '5.21'


@pytest.mark.katello_agent
def test_katello_agent_remove_package(katello_agent_client, api):
    host = foreman_host(katello_agent_client, api)

    katello_agent_client.run_expect([0], 'yum -y install gorilla')
    gorilla = katello_agent_client.package('gorilla')
    assert gorilla.is_installed

    task = api.resource('host_packages').call('remove', {'host_id': host['id'], 'packages': ['gorilla']})
    wait_for_task(task, api)
    gorilla = katello_agent_client.package('gorilla')
    assert not gorilla.is_installed


@pytest.mark.containers
def test_fetch_container_content(katello_client, entities, registration_hostname, os_release_major, user):
    if os_release_major == "6":
        pytest.skip("container content not supported on EL6")

    container_label = f"{entities['organization_label']}-{entities['product_label']}-{entities['container_repository_label']}".lower()
    docker_connection = f"docker://{registration_hostname}/{container_label}"

    katello_client.run('yum -y install skopeo')
    katello_client.run('mkdir containers')
    katello_client.run_expect([0], f"curl -O http://{registration_hostname}/pub/katello-server-ca.crt")
    katello_client.run_expect([1], f"skopeo copy {docker_connection} dir:containers --src-creds doesnotexist:changeme --src-cert-dir .")
    katello_client.run_expect([0], f"skopeo copy {docker_connection} dir:containers --src-creds {user.username}:{user.password} --src-cert-dir .")
    katello_client.run_expect([1], f"skopeo copy docker://{registration_hostname}/{container_label} dir:containers --src-cert-dir .")
