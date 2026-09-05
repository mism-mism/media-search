from media_search.domain.frames import (
    MAX_REPRESENTATIVE_FRAMES,
    SHORT_VIDEO_THRESHOLD_SECONDS,
    representative_frame_positions,
)


def test_short_video_uses_single_middle_frame():
    positions = representative_frame_positions(4.9)
    assert len(positions) == 1
    assert positions[0].position == 0.5


def test_five_seconds_or_more_uses_max_three_uniform_including_ends():
    positions = representative_frame_positions(SHORT_VIDEO_THRESHOLD_SECONDS)
    assert len(positions) == MAX_REPRESENTATIVE_FRAMES
    assert [p.position for p in positions] == [0.0, 0.5, 1.0]


def test_longer_video_same_count():
    positions = representative_frame_positions(120.0)
    assert [p.position for p in positions] == [0.0, 0.5, 1.0]


def test_negative_duration_rejected():
    try:
        representative_frame_positions(-1.0)
        assert False, "expected ValueError"
    except ValueError:
        pass
