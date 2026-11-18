from pathlib import Path

import pytest
from PIL import Image

from editor import GifProject


@pytest.fixture()
def source(tmp_path):
    images = [Image.new('RGBA', (24, 20), color) for color in
              ('#ff0000', '#00ff00', '#0000ff', '#ffff00', '#00ffff')]
    filename = tmp_path / 'original.gif'
    images[0].save(filename, format='GIF', save_all=True,
                   append_images=images[1:], duration=[100, 220, 80, 300, 100],
                   loop=0, disposal=2, optimize=False)
    return filename


def test_cut_middle_and_undo_redo(source):
    p = GifProject(source)
    assert p.count == 5
    assert p.total_ms == 800
    assert p.index_at_time(0) == 0
    assert p.index_at_time(100) == 1
    assert p.index_at_time(320) == 2
    assert p.cut(1, 3) == 3
    assert p.kept == [0, 4]
    assert p.total_ms == 200
    assert p.can_undo and not p.can_redo
    assert p.undo()
    assert p.kept == [0, 1, 2, 3, 4]
    assert p.redo()
    assert p.kept == [0, 4]
    assert not source.stat().st_size == 0
    p.close()


def test_export_keeps_only_remaining_frames_and_original(source, tmp_path):
    p = GifProject(source)
    p.cut(1, 2)
    destination = tmp_path / 'result.gif'
    p.export(destination)
    p.close()
    out = GifProject(destination)
    assert out.count == 3
    assert out.durations == [100, 300, 100]
    colors = [out.image(i).convert('RGB').getpixel((5, 5)) for i in range(out.count)]
    assert colors == [(255, 0, 0), (255, 255, 0), (0, 255, 255)]
    assert GifProject(source).count == 5
    out.close()


def test_disallows_deleting_every_frame(source):
    p = GifProject(source)
    with pytest.raises(ValueError, match='všechny'):
        p.cut(0, 4)
    with pytest.raises(ValueError):
        p.cut(3, 1)
    assert p.count == 5
    with pytest.raises(ValueError, match='přepsat'):
        p.export(source)
    p.close()


def test_reset_and_multiple_cuts(source):
    p = GifProject(source)
    p.cut(0, 0)
    p.cut(1, 1)
    p.cut(p.count-1, p.count-1)
    assert p.kept == [1, 3]
    p.reset()
    assert p.count == 5
    assert p.undo()
    assert p.kept == [1, 3]
    p.close()


def test_invalid_file(tmp_path):
    path = tmp_path / 'bad.gif'
    path.write_text('not a gif')
    with pytest.raises(ValueError):
        GifProject(path)
    with pytest.raises(FileNotFoundError):
        GifProject(tmp_path / 'absent.gif')
