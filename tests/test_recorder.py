import shutil
import pytest
from PIL import Image
from recorder import RecordingSession, RecorderError
from editor import GifProject


def test_region_validation():
    with pytest.raises(ValueError):
        RecordingSession(50, 100, 12)
    with pytest.raises(ValueError):
        RecordingSession(200, 100, 31)


def test_frame_validation():
    r = RecordingSession(80, 60, 10)
    with pytest.raises(RecorderError, match='spuštěno'):
        r.write_rgba(b'abc')


@pytest.mark.skipif(not shutil.which('ffmpeg'), reason='FFmpeg not installed')
def test_end_to_end_record_pause_export(tmp_path):
    r = RecordingSession(80, 60, 10)
    try:
        r.start()
        red = bytes((250, 10, 20, 255)) * (80 * 60)
        green = bytes((10, 250, 20, 255)) * (80 * 60)
        r.write_rgba(red)
        r.pause()
        r.write_rgba(green)
        r.resume()
        for _ in range(2):
            r.write_rgba(green)
        r.stop()
        dest = r.encode_gif(tmp_path/'result.gif')
        assert dest.exists() and dest.stat().st_size > 100
        p = GifProject(dest)
        assert p.total_ms >= 200
        assert p.count >= 2
        p.close()
    finally:
        r.cleanup()


def test_encoding_queue_never_blocks_producer(tmp_path, monkeypatch):
    """A slow ffmpeg encoder must drop frames instead of freezing Qt's GUI."""
    import time
    import threading
    from recorder import EncodingQueue, RecordingSession

    received = []
    original_start = RecordingSession.start
    original_stop = RecordingSession.stop
    original_write = RecordingSession.write_rgba
    original_cleanup = RecordingSession.cleanup

    def fake_start(self):
        self.started = time.monotonic()
        self.proc = object()  # mimics a running encoder for elapsed_seconds

    def fake_write(self, pixels):
        time.sleep(.08)
        received.append(pixels)
        self.frames += 1

    def fake_stop(self):
        self.proc = None
        return tmp_path/'fake.mkv'

    monkeypatch.setattr(RecordingSession, 'start', fake_start)
    monkeypatch.setattr(RecordingSession, 'write_rgba', fake_write)
    monkeypatch.setattr(RecordingSession, 'stop', fake_stop)
    monkeypatch.setattr(RecordingSession, 'cleanup', lambda self: None)
    writer = EncodingQueue(80, 60, 10)
    frame = b'x'*80*60*4
    t0 = time.monotonic()
    for _ in range(20):
        writer.write(frame)
    elapsed = time.monotonic() - t0
    assert elapsed < .3, 'GUI should never wait for pipe.write()'
    assert writer.dropped >= 10
    assert writer.finalize('') == ''
    assert len(received) >= 1
    assert writer.thread.is_alive() is False


def test_queue_end_to_end_ffmpeg(tmp_path):
    import shutil
    from recorder import EncodingQueue
    if not shutil.which('ffmpeg'):
        pytest.skip('ffmpeg not available')
    writer = EncodingQueue(80, 60, 10)
    try:
        frame = bytes((10, 220, 90, 255)) * (80 * 60)
        for _ in range(3):
            writer.write(frame)
        gif = writer.finalize(str(tmp_path/'queued.gif'))
        assert gif and (tmp_path/'queued.gif').exists()
    finally:
        writer.session.cleanup()
