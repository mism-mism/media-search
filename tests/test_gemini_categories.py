import json

import pytest

from test_gemini_annotator import Session, png, response
from media_search.adapters.gemini_categories import GeminiCategoryClassifier, normalize_reference
from media_search.domain.categories import ReferenceCategory, catalog_version
from media_search.ports.categories import CategoryClassificationError


def categories():
    return [ReferenceCategory('a', '容器', 'ポンプが見える', (normalize_reference(png()),)),
            ReferenceCategory('b', '手持ち', '人の手で対象を持っている', (normalize_reference(png()),))]


def decisions():
    return [{'category_id': 'a', 'outcome': 'match', 'reason': 'ポンプが見える'},
            {'category_id': 'b', 'outcome': 'uncertain', 'reason': '手の形が不鮮明'}]


def test_multimodal_request_and_complete_structured_judgments():
    session = Session(response(json.dumps({'decisions': decisions()})))
    result = GeminiCategoryClassifier(project='p', session_factory=lambda: session).classify(png(), categories())
    assert result.catalog_version == catalog_version(categories())
    assert result.tags == ('容器',)
    assert result.decisions[1].outcome == 'uncertain'
    url, options = session.calls[0]
    assert url.startswith('https://aiplatform.googleapis.com/v1/projects/p/')
    assert options['timeout'] == 45 and options['allow_redirects'] is False
    payload = options['json']
    parts = payload['contents'][0]['parts']
    assert sum('inlineData' in p for p in parts) == 3
    assert '判定対象' in parts[-2]['text']
    assert '見本' in parts[0]['text']
    assert payload['generationConfig']['maxOutputTokens'] <= 2048
    assert 'tools' not in payload


@pytest.mark.parametrize('bad', [[], decisions()[:1], decisions() + decisions()[:1],
    [dict(decisions()[0], category_id='unknown'), decisions()[1]],
    [dict(decisions()[0], outcome='yes'), decisions()[1]],
    [dict(decisions()[0], reason='x' * 201), decisions()[1]],
    [dict(decisions()[0], name='invented'), decisions()[1]],
    [dict(decisions()[0], reason=3), decisions()[1]]])
def test_malformed_or_missing_decisions_reject_whole_report(bad):
    session = Session(response(json.dumps({'decisions': bad})))
    with pytest.raises(CategoryClassificationError, match='classification_failed'):
        GeminiCategoryClassifier(project='p', session_factory=lambda: session).classify(png(), categories())
    assert len(session.calls) == 1


@pytest.mark.parametrize('session', [Session(status=429), Session(error=TimeoutError('secret')),
    Session(response('{}', 'MAX_TOKENS')), Session({})])
def test_provider_failures_are_safe_and_not_retried(session):
    with pytest.raises(CategoryClassificationError) as error:
        GeminiCategoryClassifier(project='p', session_factory=lambda: session).classify(png(), categories())
    assert str(error.value) == 'classification_failed'
    assert len(session.calls) == 1


def test_reference_rejects_invalid_bytes_without_provider():
    with pytest.raises(ValueError):
        normalize_reference(b'not image')
