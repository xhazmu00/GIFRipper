"""Frame-accurate selection conversions for the GIF editor.

All range endpoints are inclusive *frames*. The time shown for OD is the
beginning of that frame; time DO is the exclusive end of the final frame.
The timeline uses boundaries rather than frame centers, allowing a one-frame
selection to remain visibly wide and the handles to sit at both its ends.
This module has no Qt or recording dependencies.
"""
from __future__ import annotations

from bisect import bisect_left, bisect_right


def _fraction(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def boundary_fraction(prefix_ms: list[int], boundary: int, unit: str) -> float:
    count = len(prefix_ms) - 1
    if count <= 0:
        return 0.0
    boundary = max(0, min(boundary, count))
    if unit == 'time':
        return prefix_ms[boundary] / max(1, prefix_ms[-1])
    return boundary / count


def nearest_boundary(prefix_ms: list[int], fraction: float, unit: str) -> int:
    """Closest timeline boundary (0..frame count) by display position."""
    count = len(prefix_ms) - 1
    if count <= 0:
        return 0
    fraction = _fraction(fraction)
    if unit != 'time':
        return min(count, max(0, round(fraction * count)))
    target = fraction * prefix_ms[-1]
    pos = bisect_left(prefix_ms, target)
    if pos <= 0:
        return 0
    if pos >= len(prefix_ms):
        return count
    return pos - 1 if (target - prefix_ms[pos - 1] <= prefix_ms[pos] - target) else pos


def frame_at_fraction(prefix_ms: list[int], fraction: float, unit: str) -> int:
    count = len(prefix_ms) - 1
    if count <= 1:
        return 0
    fraction = _fraction(fraction)
    if unit != 'time':
        return min(count - 1, int(fraction * count))
    t = min(prefix_ms[-1] - 1, int(fraction * prefix_ms[-1]))
    return min(count - 1, max(0, bisect_right(prefix_ms, t) - 1))


def start_frame_at_ms(prefix_ms: list[int], timestamp_ms: int) -> int:
    """Frame containing selected start time. A boundary selects the next frame."""
    return frame_at_fraction(prefix_ms, max(0, int(timestamp_ms)) / max(1, prefix_ms[-1]), 'time')


def end_frame_at_ms(prefix_ms: list[int], timestamp_ms: int) -> int:
    """Last included frame. An exact boundary excludes the following frame."""
    count = len(prefix_ms) - 1
    if count <= 1:
        return 0
    t = max(0, min(prefix_ms[-1] - 1, int(timestamp_ms) - 1))
    return max(0, min(count - 1, bisect_right(prefix_ms, t) - 1))


def selection_duration_ms(prefix_ms: list[int], first: int, last: int) -> int:
    return prefix_ms[last + 1] - prefix_ms[first]


def format_timestamp(ms: int, *, milliseconds: bool = True) -> str:
    ms = max(0, int(ms))
    minutes, rem = divmod(ms, 60_000)
    seconds, fraction = divmod(rem, 1_000)
    hrs, minutes = divmod(minutes, 60)
    result = f'{hrs:02}:{minutes:02}:{seconds:02}' if hrs else f'{minutes:02}:{seconds:02}'
    return result + (f'.{fraction:03}' if milliseconds else '')
