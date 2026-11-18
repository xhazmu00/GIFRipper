"""Locale-independent newline-delimited JSON transport for the capture helper.

Windows often gives a redirected Python stdout a legacy codepage such as
cp1250. Text-mode writes with ``ensure_ascii=False`` could therefore produce
non-UTF-8 bytes, which the Qt GUI rightfully rejected as malformed JSON IPC.

Always transmit ASCII-only JSON (Unicode values use JSON backslash-u escapes),
and write to the binary pipe to bypass *any* OS text encoding entirely.
The wire format remains valid UTF-8 and preserves all original Unicode values.
"""
from __future__ import annotations

import json


def encode_packet(packet: dict) -> bytes:
    if not isinstance(packet, dict):
        raise TypeError('IPC packet must be a JSON object')
    return (json.dumps(packet, ensure_ascii=True, separators=(',', ':')) + '\n').encode('ascii')


def decode_packet(line: bytes) -> dict:
    packet = json.loads(line.decode('utf-8'))
    if not isinstance(packet, dict):
        raise ValueError('IPC packet must be a JSON object')
    return packet
