import importlib
from io import BytesIO
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from media_search.domain.categories import CategoryReport, CategoryDecision, catalog_version


def png():
    out = BytesIO()
    Image.new('RGB', (16, 16), 'red').save(out, 'PNG')
    return out.getvalue()


@pytest.fixture
def runtime(monkeypatch, tmp_path):
    for key in ('MEDIA_SEARCH_DB_GCS', 'CLOUD_RUN_IMPORT_JOB', 'IMPORT_JOB_BACKEND', 'MEDIA_SEARCH_DB', 'MEDIA_SEARCH_MEDIA_ROOT', 'MEDIA_SEARCH_WORK'):
        monkeypatch.delenv(key, raising=False)
    for key, value in {'MEDIA_SEARCH_DATA': str(tmp_path), 'EMBEDDER': 'fake', 'MEDIA_BACKEND': 'local',
                       'FRAME_BACKEND': 'local', 'IMPORT_LOCK_BACKEND': 'fs', 'IMAGE_ANNOTATION_BACKEND': 'off'}.items():
        monkeypatch.setenv(key, value)
    return importlib.import_module('media_search.main').build_runtime()


def client_for(rt):
    from media_search.api.app import create_app
    return TestClient(create_app(search=rt.search, importer=rt.importer, library=rt.library,
                                 metadata=rt.metadata, media_storage=rt.media_storage, categories=rt.categories))


def create(client, name='容器', data=None, files=None):
    return client.post('/api/library/categories', data=data or {'name': name, 'criteria': '対象が写っている'},
                       files=files if files is not None else [('references', ('example.png', png(), 'image/png'))])


def test_management_preview_search_and_deletion_invalidation(runtime):
    client = client_for(runtime)
    created = create(client)
    assert created.status_code == 201
    item = created.json()
    assert item['name'] == '容器'
    assert 'references' not in item  # never expose base64 through list JSON
    preview = client.get(item['reference_urls'][0])
    assert preview.status_code == 200 and preview.headers['content-type'] == 'image/jpeg'
    listing = client.get('/api/library/categories').json()
    assert listing['categories'] == [item]
    assert listing['enabled'] is False
    runtime.media_storage.put_bytes('photo.png', png(), content_type='image/png')
    runtime.importer.execute_storage(runtime.media_storage)
    categories = runtime.categories.list_all()
    report = CategoryReport(catalog_version(categories), (CategoryDecision(item['category_id'], '容器', 'match', '確認'),), 'test', 'v1')
    runtime.metadata.upsert(replace(runtime.metadata.get('photo.png'), category_report=report))
    assert client.get('/api/library/assets').json()['assets'][0]['category_report']['decisions'][0]['name'] == '容器'
    assert client.get('/api/assets/photo.png').json()['category_status'] == 'ready'
    for method in ('get', 'post'):
        args = {'params': {'q': '容器', 'tags': ['容器']}} if method == 'get' else {'json': {'q': '容器', 'tags': ['容器']}}
        results = getattr(client, method)('/api/search', **args).json()['results']
        assert results[0]['asset_id'] == 'photo.png'
        assert results[0]['category_report']['decisions'][0]['outcome'] == 'match'
    assert client.delete('/api/library/categories/' + item['category_id']).status_code == 200
    assert runtime.metadata.get('photo.png').category_report is None
    assert client.get('/api/search', params={'q': '容器', 'tags': '容器'}).json()['results'] == []
    assert client.get(item['reference_urls'][0]).status_code == 404


def test_duplicate_invalid_images_and_caps(runtime):
    client = client_for(runtime)
    assert create(client).status_code == 201
    assert create(client).status_code == 400
    assert create(client, files=[('references', ('bad.png', b'<script>', 'image/png'))]).status_code == 400
    assert create(client, files=[('references', ('x.png', png(), 'image/png'))] * 4).status_code == 400
    assert create(client, data={'name': 'a' * 41, 'criteria': '基準'}).status_code == 400
    assert create(client, data={'name': 'a', 'criteria': ' '}).status_code == 400
    assert create(client, files=[('references', ('big.png', b'x' * (30 * 1024 * 1024 + 1), 'image/png'))]).status_code == 413
    for i in range(4):
        assert create(client, name=f'category{i}').status_code == 201
    assert create(client, name='sixth').status_code == 400
    assert len(client.get('/api/library/categories').json()['categories']) == 5


def test_busy_mutation_returns_safe_409(runtime):
    client = client_for(runtime)
    assert runtime.import_lock.try_acquire('private-import-holder')
    try:
        result = create(client)
        assert result.status_code == 409
        assert result.json()['detail'] == {'error': 'import_busy'}
        assert runtime.categories.list_all() == []
    finally:
        runtime.import_lock.release('private-import-holder')


def test_mutation_reloads_and_persists_while_holding_lock(runtime):
    events = []
    service = runtime.categories
    service._reload = lambda: events.append(('reload', runtime.import_lock.current_holder()))
    service._persist = lambda: events.append(('persist', runtime.import_lock.current_holder()))
    assert create(client_for(runtime)).status_code == 201
    assert [e[0] for e in events] == ['reload', 'persist']
    assert all(e[1] for e in events)
    assert runtime.import_lock.current_holder() is None


def test_ui_has_visible_category_registration_and_safe_judgment_renderer(runtime):
    html = client_for(runtime).get('/').text
    assert 'id="categoriesTab"' in html
    assert 'id="categoryForm"' in html
    assert '見本画像' in html and '判定基準' in html
    assert 'esc(d.name)' in html and 'esc(d.reason)' in html


def test_runtime_reload_replaces_catalog_and_mutation_persists_current_snapshot(runtime, monkeypatch, tmp_path):
    from media_search.adapters import gcs_db_sync
    import shutil
    remote = tmp_path / 'remote.sqlite'
    events = []
    def download(*, gcs_uri, local_path):
        if remote.exists():
            shutil.copyfile(remote, local_path)
    def upload(*, gcs_uri, local_path):
        events.append('upload')
        shutil.copyfile(local_path, remote)
    monkeypatch.setattr(gcs_db_sync, 'download_db_if_remote', download)
    monkeypatch.setattr(gcs_db_sync, 'upload_db', upload)
    monkeypatch.setenv('MEDIA_SEARCH_DB_GCS', 'gs://test/state.db')
    module = importlib.import_module('media_search.main')
    one = module.build_runtime()
    assert create(client_for(one), name='最初').status_code == 201
    # A second runtime sees the persisted catalog and saves its own update.
    monkeypatch.setenv('MEDIA_SEARCH_DB', str(tmp_path / 'second.sqlite'))
    two = module.build_runtime()
    assert create(client_for(two), name='次のカテゴリ').status_code == 201
    one.reload_db()
    assert {c.name for c in one.categories.list_all()} == {'最初', '次のカテゴリ'}
    assert one.importer._categories.list_all() == one.categories.list_all()
    assert events == ['upload', 'upload']
