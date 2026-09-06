from dataclasses import replace

import pytest
from PIL import Image

from media_search.domain.categories import ReferenceCategory, CategoryDecision, CategoryReport, catalog_version
from media_search.adapters.sqlite_categories import SqliteCategoryRepository
from media_search.adapters.sqlite_store import SqliteMetadataRepository, open_db
from media_search.adapters.local_media_storage import LocalMediaStorage
from media_search.adapters.media_probe import LocalMediaProbe
from media_search.adapters.memory_store import InMemoryVectorSearch
from media_search.application.import_directory import ImportDirectory
from media_search.ports.embedding import FakeEmbedder
from media_search.ports.categories import CategoryClassificationError


def category(name='ポンプ容器'):
    return ReferenceCategory('cat1', name, 'ポンプの付いた容器が写っている', (b'jpeg',))


class Catalog:
    def __init__(self):
        self.items = [category()]
    def list_all(self):
        return self.items


class Classifier:
    def __init__(self, outcome='match'):
        self.calls = 0
        self.fail = False
        self.outcome = outcome
    def classify(self, image_bytes, categories):
        self.calls += 1
        if self.fail:
            raise CategoryClassificationError('private provider error')
        return CategoryReport(catalog_version(categories), tuple(
            CategoryDecision(c.category_id, c.name, self.outcome, '容器の形を確認') for c in categories
        ), 'fake', 'v1')


def setup(tmp_path, count=1):
    root = tmp_path / 'source'
    root.mkdir()
    for i in range(count):
        Image.new('RGB', (12, 12), 'white').save(root / f'{i}.png')
    conn = open_db(tmp_path / 'db.sqlite')
    meta = SqliteMetadataRepository(conn)
    vectors = InMemoryVectorSearch()
    kwargs = dict(metadata=meta, vectors=vectors, embedder=FakeEmbedder(), media_probe=LocalMediaProbe(), embed_workers=4)
    return LocalMediaStorage(root), meta, vectors, kwargs


@pytest.mark.parametrize('outcome,expected', [('match', True), ('no_match', False), ('uncertain', False)])
def test_import_persists_only_positive_category_tags(tmp_path, outcome, expected):
    storage, meta, vectors, kwargs = setup(tmp_path)
    catalog, classifier = Catalog(), Classifier(outcome)
    importer = ImportDirectory(**kwargs, categories=catalog, classifier=classifier)
    importer.execute_storage(storage)
    saved = meta.get('0.png')
    assert saved.category_status == 'ready'
    assert ('ポンプ容器' in saved.search_tags) is expected
    assert bool(meta.search_text('ポンプ容器')) is expected
    assert saved.tags == []
    assert saved.category_report.decisions[0].outcome == outcome
    meta.replace_connection(open_db(tmp_path / 'db.sqlite'))
    assert meta.get('0.png').category_report == saved.category_report


def test_reimport_reuses_classification_without_reembedding_and_retries_failure(tmp_path):
    storage, meta, vectors, kwargs = setup(tmp_path)
    ImportDirectory(**kwargs).execute_storage(storage)
    meta.upsert(replace(meta.get('0.png'), tags=['手動'], product_id='sku'))
    before = vectors._frames['0.png::0']
    def no_embed(_):
        raise AssertionError('metadata-only classification re-embedded')
    kwargs['embedder'].embed_image = no_embed
    catalog, classifier = Catalog(), Classifier()
    classifier.fail = True
    importer = ImportDirectory(**kwargs, categories=catalog, classifier=classifier)
    importer.execute_storage(storage)
    assert meta.get('0.png').category_status == 'failed'
    assert meta.get('0.png').category_error == 'classification_failed'
    classifier.fail = False
    importer.execute_storage(storage)
    importer.execute_storage(storage)
    assert classifier.calls == 2
    assert vectors._frames['0.png::0'] is before
    assert meta.get('0.png').tags == ['手動']
    assert meta.get('0.png').product_id == 'sku'
    catalog.items = [replace(category(), name='新カテゴリ')]
    importer.execute_storage(storage)
    assert classifier.calls == 3
    assert meta.get('0.png').search_tags == ['手動', '新カテゴリ']


def test_classification_cap_and_empty_catalog_make_no_extra_calls(tmp_path):
    storage, meta, vectors, kwargs = setup(tmp_path, 6)
    catalog, classifier = Catalog(), Classifier()
    importer = ImportDirectory(**kwargs, categories=catalog, classifier=classifier, max_classifications=2)
    importer.execute_storage(storage)
    assert classifier.calls == 2
    assert sum(a.category_status == 'deferred' for a in meta.list_all()) == 4
    assert all(vectors.has_frames(a.asset_id) for a in meta.list_all())
    importer.execute_storage(storage)
    assert classifier.calls == 4
    catalog.items = []
    importer.execute_storage(storage)
    assert classifier.calls == 4


def test_changed_media_clears_stale_matches_on_failure(tmp_path):
    storage, meta, vectors, kwargs = setup(tmp_path)
    classifier = Classifier()
    importer = ImportDirectory(**kwargs, categories=Catalog(), classifier=classifier)
    importer.execute_storage(storage)
    Image.new('RGB', (45, 35), 'blue').save(tmp_path / 'source' / '0.png')
    classifier.fail = True
    importer.execute_storage(storage)
    assert meta.get('0.png').category_report is None
    assert meta.get('0.png').category_status == 'failed'
    assert not meta.search_text('ポンプ容器')
    assert vectors.has_frames('0.png')


def test_catalog_changes_atomically_invalidate_and_survive_reload(tmp_path):
    storage, meta, vectors, kwargs = setup(tmp_path)
    catalog = SqliteCategoryRepository(meta._conn)
    catalog.create(category())
    ImportDirectory(**kwargs, categories=catalog, classifier=Classifier()).execute_storage(storage)
    assert meta.search_text('ポンプ容器')
    with pytest.raises(ValueError):
        catalog.create(replace(category(), category_id='cat2'))
    assert meta.search_text('ポンプ容器')  # rejected change does not invalidate
    catalog.create(replace(category(), category_id='cat2', name='別カテゴリ'))
    assert not meta.search_text('ポンプ容器')
    catalog.replace_connection(open_db(tmp_path / 'db.sqlite'))
    assert len(catalog.list_all()) == 2
    catalog.delete('cat1')
    assert [c.category_id for c in catalog.list_all()] == ['cat2']


@pytest.mark.parametrize('failure', [False, True])
def test_equal_length_replacement_invalidates_category_observation(tmp_path, failure):
    storage, meta, vectors, kwargs = setup(tmp_path)
    path = tmp_path / 'source' / '0.png'
    Image.new('RGB', (12, 12), 'red').save(path, compress_level=0)
    original_bytes = path.read_bytes()
    classifier = Classifier()
    importer = ImportDirectory(**kwargs, categories=Catalog(), classifier=classifier)
    importer.execute_storage(storage)
    Image.new('RGB', (12, 12), 'blue').save(path, compress_level=0)
    assert path.read_bytes() != original_bytes and len(path.read_bytes()) == len(original_bytes)
    classifier.outcome = 'no_match'
    classifier.fail = failure
    importer.execute_storage(storage)
    assert classifier.calls == 2
    assert 'ポンプ容器' not in meta.get('0.png').search_tags
    assert meta.get('0.png').category_status == ('failed' if failure else 'ready')
    importer.execute_storage(storage)
    assert classifier.calls == (3 if failure else 2)


def test_equal_length_replacement_clears_stale_match_when_budget_deferred(tmp_path):
    storage, meta, vectors, kwargs = setup(tmp_path, 2)
    for path in (tmp_path / 'source').glob('*.png'):
        Image.new('RGB', (12, 12), 'red').save(path, compress_level=0)
    catalog, classifier = Catalog(), Classifier()
    ImportDirectory(**kwargs, categories=catalog, classifier=classifier).execute_storage(storage)
    for path in (tmp_path / 'source').glob('*.png'):
        Image.new('RGB', (12, 12), 'blue').save(path, compress_level=0)
    classifier.outcome = 'no_match'
    ImportDirectory(**kwargs, categories=catalog, classifier=classifier, max_classifications=1).execute_storage(storage)
    assert classifier.calls == 3
    assert sum(a.category_status == 'deferred' for a in meta.list_all()) == 1
    assert all('ポンプ容器' not in a.search_tags for a in meta.list_all())
