import json
from io import BytesIO

import pytest
from PIL import Image

from media_search.adapters.gemini_annotator import GeminiImageAnnotator
from media_search.ports.annotation import ImageAnnotationError


class Session:
    def __init__(self, payload=None, status=200, error=None):
        self.payload = payload
        self.status = status
        self.error = error
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        if self.error:
            raise self.error
        return self

    @property
    def status_code(self):
        return self.status

    def json(self):
        return self.payload


def png():
    out = BytesIO()
    Image.new("RGBA", (2000, 1000), (255, 255, 255, 255)).save(out, "PNG")
    return out.getvalue()


def response(text, finish="STOP"):
    return {"candidates": [{"finishReason": finish, "content": {"parts": [{"text": text}]}}]}


def test_request_uses_bounded_image_schema_and_fixed_google_endpoint():
    import base64
    session = Session(response(json.dumps({"tags": ["白いボトル", "白いボトル"], "description": "白い容器。"})))
    result = GeminiImageAnnotator(project="test-project", session_factory=lambda: session).annotate(png())
    assert result.tags == ("白いボトル",)
    assert result.description == "白い容器。"
    assert result.model_id == "gemini-3.1-flash-lite"
    url, options = session.calls[0]
    assert url == "https://aiplatform.googleapis.com/v1/projects/test-project/locations/global/publishers/google/models/gemini-3.1-flash-lite:generateContent"
    assert options["timeout"] == 45
    assert options["allow_redirects"] is False
    payload = options["json"]
    assert payload["generationConfig"]["responseMimeType"] == "application/json"
    assert payload["generationConfig"]["responseSchema"]["required"] == ["tags", "description"]
    assert payload["generationConfig"]["maxOutputTokens"] <= 2048
    inline = payload["contents"][0]["parts"][0]["inlineData"]
    assert inline["mimeType"] == "image/jpeg"
    with Image.open(BytesIO(base64.b64decode(inline["data"]))) as image:
        assert max(image.size) <= 1024
    assert "systemInstruction" in payload
    assert "tools" not in payload


@pytest.mark.parametrize("payload", [
    {}, {"promptFeedback": {"blockReason": "SAFETY"}},
    response("not json"), response('{"tags":[],"description":""}'),
    response('{"tags":[1],"description":"白い容器"}'),
    response('{"tags":["白"],"description":"容器","product_id":"guessed"}'),
    response('{"tags":["白"],"description":"容器"}', "MAX_TOKENS"),
    response('{"tags":["白"],"description":' + json.dumps("長" * 301) + '}'),
])
def test_invalid_or_refused_output_is_safe_failure(payload):
    session = Session(payload)
    with pytest.raises(ImageAnnotationError, match="generation_failed"):
        GeminiImageAnnotator(project="p", session_factory=lambda: session).annotate(png())
    assert len(session.calls) == 1


@pytest.mark.parametrize("session", [Session(status=429), Session(status=403), Session(error=TimeoutError("private provider details"))])
def test_provider_failures_do_not_retry_or_expose_details(session):
    with pytest.raises(ImageAnnotationError) as exc:
        GeminiImageAnnotator(project="p", session_factory=lambda: session).annotate(png())
    assert str(exc.value) == "generation_failed"
    assert len(session.calls) == 1


def test_endpoint_configuration_rejects_path_injection():
    with pytest.raises(ValueError):
        GeminiImageAnnotator(project="test/../../other")


def test_invalid_image_never_calls_provider():
    session = Session()
    with pytest.raises(ImageAnnotationError):
        GeminiImageAnnotator(project="p", session_factory=lambda: session).annotate(b"invalid")
    assert not session.calls
