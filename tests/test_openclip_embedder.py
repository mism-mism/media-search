import os

import pytest


@pytest.mark.skipif(
    os.environ.get("RUN_OPENCLIP_SMOKE") != "1",
    reason="set RUN_OPENCLIP_SMOKE=1 to load OpenCLIP",
)
def test_openclip_text_image_same_dim():
    from media_search.adapters.openclip_embedder import OpenClipEmbedder
    from PIL import Image
    import io

    emb = OpenClipEmbedder()
    img = Image.new("RGB", (64, 64), (200, 20, 20))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    iv = emb.embed_image(buf.getvalue())
    tv = emb.embed_text("a red square")
    assert iv.shape == tv.shape
    assert iv.shape[0] == emb.dimension
    assert emb.dimension >= 256
