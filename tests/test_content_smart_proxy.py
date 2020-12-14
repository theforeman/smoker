import pytest


@pytest.fixture
def content_smart_proxy(api, organization):
    smart_proxies = api.resource('smart_proxies').call('index')
    content_proxy = {}

    for proxy in smart_proxies['results']:
        for feature in proxy['features']:
            if feature['name'] == 'Pulp Node':
                content_proxy = proxy
                break

    content_proxy_id = content_proxy['id']

    environments = api.resource('capsule_content').call('lifecycle_environments', {
        'id': content_proxy['id']
    })['results']

    for environment in environments:
        api.resource('capsule_content').call('remove_lifecycle_environment', {
            'id': content_proxy_id,
            'environment_id': environment['id']
        })

    library = api.resource('lifecycle_environments').call('index', {
        'search': 'Library',
        'organization_id': organization['id']
    })['results'][0]

    api.resource('capsule_content').call('add_lifecycle_environment', {
        'id': content_proxy_id,
        'environment_id': library['id']
    })

    return content_proxy


@pytest.fixture
def organization(api, entities):
    return api.resource('organizations').call('index', {
        'search': entities['organization_label']
    })['results'][0]


def test_smart_proxy_content_sync(api, content_smart_proxy):
    task = api.resource('capsule_content').call('sync', {'id': content_smart_proxy['id']})
    task = wait_for_task(task, api)
    assert task['result'] == 'success'
