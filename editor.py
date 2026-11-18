"""Non-destructive, frame-accurate GIF editing engine.

A project stores a list of indexes into the original GIF. Cuts never modify
source data and can be undone. Durations are inherited from source frames.
"""

from __future__ import annotations

from bisect import bisect_right
from functools import lru_cache
import os
from pathlib import Path
import tempfile

from PIL import Image, UnidentifiedImageError


class GifProject:
    def __init__(self, filename: str | os.PathLike[str]):
        self.path = Path(filename).expanduser().resolve()
        if not self.path.is_file():
            raise FileNotFoundError(self.path)
        try:
            self._image = Image.open(self.path)
            if self._image.format != 'GIF':
                raise ValueError('Soubor není GIF.')
            self.size = self._image.size
            self.frame_count = getattr(self._image, 'n_frames', 1)
            self.durations: list[int] = []
            for i in range(self.frame_count):
                self._image.seek(i)
                # GIF delays are in hundredths of a second. Zero-delay files
                # otherwise create a busy loop in our UI.
                self.durations.append(max(20, int(self._image.info.get('duration', 100) or 100)))
        except (UnidentifiedImageError, OSError, EOFError) as exc:
            raise ValueError(f'GIF nejde načíst: {exc}') from exc
        self.kept = list(range(self.frame_count))
        self._undo: list[list[int]] = []
        self._redo: list[list[int]] = []
        self._update_timeline()

    @lru_cache(maxsize=48)
    def source_image(self, original_index: int) -> Image.Image:
        if not (0 <= original_index < self.frame_count):
            raise IndexError('Snímek mimo rozsah')
        self._image.seek(original_index)
        # Pillow reconstructs composited GIF frames respecting disposal,
        # so deleted incremental frames do not create rendering artifacts.
        return self._image.convert('RGBA').copy()

    def image(self, edited_index: int) -> Image.Image:
        return self.source_image(self.kept[edited_index])

    @property
    def count(self) -> int:
        return len(self.kept)

    def duration(self, edited_index: int) -> int:
        return self.durations[self.kept[edited_index]]

    def _update_timeline(self) -> None:
        self.prefix_ms = [0]
        for i in self.kept:
            self.prefix_ms.append(self.prefix_ms[-1] + self.durations[i])

    @property
    def total_ms(self) -> int:
        return self.prefix_ms[-1]

    def position_ms(self, edited_index: int) -> int:
        return self.prefix_ms[edited_index]

    def index_at_time(self, time_ms: int) -> int:
        return max(0, min(self.count - 1, bisect_right(self.prefix_ms, time_ms) - 1))

    def _save_undo(self) -> None:
        self._undo.append(self.kept.copy())
        if len(self._undo) > 50:
            self._undo.pop(0)
        self._redo.clear()

    @property
    def can_undo(self) -> bool:
        return bool(self._undo)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo)

    def cut(self, first: int, last: int) -> int:
        """Delete inclusive edited-frame range; retain at least one frame."""
        if not (0 <= first <= last < self.count):
            raise ValueError('Neplatný rozsah snímků.')
        if last - first + 1 == self.count:
            raise ValueError('Nelze odstranit všechny snímky.')
        self._save_undo()
        deleted = last - first + 1
        del self.kept[first:last + 1]
        self._update_timeline()
        return deleted

    def keep_range(self, first: int, last: int) -> int:
        """Keep only the inclusive selection; one undo step, original untouched.

        Returns the number of removed frames.  Selecting the complete GIF
        is a harmless no-op (and does not create a history entry).
        """
        if not (0 <= first <= last < self.count):
            raise ValueError('Neplatný rozsah snímků.')
        removed = self.count - (last - first + 1)
        if removed == 0:
            return 0
        self._save_undo()
        self.kept = self.kept[first:last + 1]
        self._update_timeline()
        return removed

    def undo(self) -> bool:
        if not self._undo:
            return False
        self._redo.append(self.kept.copy())
        self.kept = self._undo.pop()
        self._update_timeline()
        return True

    def redo(self) -> bool:
        if not self._redo:
            return False
        self._undo.append(self.kept.copy())
        self.kept = self._redo.pop()
        self._update_timeline()
        return True

    def reset(self) -> None:
        if self.count == self.frame_count and self.kept == list(range(self.frame_count)):
            return
        self._save_undo()
        self.kept = list(range(self.frame_count))
        self._update_timeline()

    def export(self, destination: str | os.PathLike[str]) -> None:
        """Encode edited timeline to a new GIF and atomically commit it.

        Pillow renders complete images (rather than GIF delta tiles), which
        allows removing a middle frame without breaking later frames.
        """
        target = Path(destination).expanduser().resolve()
        if target.suffix.lower() != '.gif':
            raise ValueError('Výstup musí mít příponu .gif')
        if target == self.path:
            raise ValueError('Původní GIF nelze přepsat. Zvol jiný název.')
        if not target.parent.is_dir():
            raise FileNotFoundError(target.parent)
        with tempfile.NamedTemporaryFile(dir=target.parent, suffix='.gif', prefix='.gifripper-', delete=False) as fp:
            temporary = Path(fp.name)
        try:
            frames = [self.image(i).copy() for i in range(self.count)]
            frames[0].save(
                temporary, format='GIF', save_all=True,
                append_images=frames[1:],
                duration=[self.duration(i) for i in range(self.count)],
                loop=0, disposal=2, optimize=True,
            )
            os.replace(temporary, target)
        finally:
            if temporary.exists():
                temporary.unlink()

    def close(self) -> None:
        self.source_image.cache_clear()
        self._image.close()
