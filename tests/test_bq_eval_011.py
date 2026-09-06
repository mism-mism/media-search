from media_search.eval.text_image_queries import hit_at_1


def test_hit_at_1_prefix():
    assert hit_at_1("01-cat.jpg", "01-cat")
    assert hit_at_1("library/x_01-cat.jpg", "01-cat")
    assert not hit_at_1("02-dog.jpg", "01-cat")
    assert not hit_at_1(None, "01-cat")
