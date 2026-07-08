import pytest
import requests


@pytest.mark.plugin('katello')
def test_foreman_product(product):
    assert product


@pytest.mark.plugin('katello')
def test_foreman_yum_repository(yum_repository, api):
    assert yum_repository
    api.resource_action('repositories', 'sync', {'id': yum_repository['id']})
    assert requests.get(f'{yum_repository["full_path"]}/repodata/repomd.xml', verify=False)
    assert requests.get(f'{yum_repository["full_path"]}/Packages/b/bear-4.1-1.noarch.rpm', verify=False)


@pytest.mark.plugin('katello')
def test_foreman_file_repository(file_repository, api):
    assert file_repository
    api.resource_action('repositories', 'sync', {'id': file_repository['id']})
    assert requests.get(f'{file_repository["full_path"]}/1.iso', verify=False)


@pytest.mark.plugin('katello')
def test_foreman_container_repository(container_repository, api):
    assert container_repository
    api.resource_action('repositories', 'sync', {'id': container_repository['id']})


@pytest.mark.plugin('katello')
def test_foreman_lifecycle_environment(lifecycle_environment):
    assert lifecycle_environment


@pytest.mark.plugin('katello')
def test_foreman_content_view(content_view, yum_repository, api):
    assert content_view
    api.update('content_views', {'id': content_view['id'], 'repository_ids': [yum_repository['id']]})
    api.resource_action('content_views', 'publish', {'id': content_view['id']})
    # do something with the published view
    versions = api.list('content_view_versions', params={'content_view_id': content_view['id']})
    for version in versions:
        current_environment_ids = {environment['id'] for environment in version['environments']}
        for environment_id in current_environment_ids:
            api.resource_action('content_views', 'remove_from_environment', params={'id': content_view['id'], 'environment_id': environment_id})
        api.delete('content_view_versions', version)


@pytest.mark.plugin('katello')
def test_foreman_manifest(organization, api, fixture_dir):
    manifest_path = fixture_dir / 'manifest.zip'
    with open(manifest_path, 'rb') as manifest_file:
        files = {'content': (str(manifest_path), manifest_file, 'application/zip')}
        params = {'organization_id': organization['id']}
        api.resource_action('subscriptions', 'upload', params, files=files)
