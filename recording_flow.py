"""Qt-independent helpers for GIFRipper's full-screen and region recording.

Preview images are in physical capture pixels; Qt mouse coordinates are in
logical pixels. Explicit mapping avoids incorrect crops on Windows at 125/150%
scaling, including monitor geometries that do not start at the virtual origin.
"""
from __future__ import annotations

import math


def fullscreen_region(width: object, height: object) -> list[int]:
    """Return complete capture image in its native pixel resolution."""
    try:
        w, h = int(width), int(height)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError('Nahrávací proces neposlal rozměry obrazovky.') from exc
    if w < 80 or h < 60:
        raise ValueError('Nahrávací proces neposlal platné rozměry obrazovky.')
    return [0, 0, w, h]


def region_from_logical_rect(start_x: float, start_y: float,
                             end_x: float, end_y: float,
                             logical_width: float, logical_height: float,
                             pixel_width: int, pixel_height: int) -> list[int]:
    """Map a mouse-drag selection to capture pixels, clipping to the screen.

    Input positions are local to the capture overlay, not global desktop
    coordinates. Rounds outward so the entire selected rectangle is recorded.
    """
    if not all(math.isfinite(v) for v in
               (start_x, start_y, end_x, end_y, logical_width, logical_height)):
        raise ValueError('Neplatné souřadnice výběru.')
    if logical_width <= 0 or logical_height <= 0:
        raise ValueError('Neplatná velikost obrazovky.')
    fullscreen_region(pixel_width, pixel_height)
    ax = min(max(0.0, min(start_x, end_x)), logical_width)
    bx = min(max(0.0, max(start_x, end_x)), logical_width)
    ay = min(max(0.0, min(start_y, end_y)), logical_height)
    by = min(max(0.0, max(start_y, end_y)), logical_height)
    x1 = max(0, min(pixel_width, math.floor(ax * pixel_width / logical_width)))
    x2 = max(0, min(pixel_width, math.ceil(bx * pixel_width / logical_width)))
    y1 = max(0, min(pixel_height, math.floor(ay * pixel_height / logical_height)))
    y2 = max(0, min(pixel_height, math.ceil(by * pixel_height / logical_height)))
    result = [x1, y1, x2 - x1, y2 - y1]
    if result[2] < 80 or result[3] < 60:
        raise ValueError('Vyber oblast alespoň 80 × 60 pixelů.')
    return result
