"""Regression tests for the cp1250/UTF-8 Windows recording failure."""
import os
from pathlib import Path
import subprocess
import sys

import pytest

from capture_ipc import decode_packet, encode_packet


def test_czech_status_roundtrip_is_ascii_and_preserves_unicode():
    data = {'event': 'status', 'phase': 'permission',
            'message': 'Čekám na přístup k obrazovce, snímkové frekvenci a nahrávání…',
            'file': r'C:\Uživatelé\Přílohy\záznam.gif'}
    wire = encode_packet(data)
    assert all(byte < 128 for byte in wire)
    assert wire.endswith(b'\n')
    assert decode_packet(wire) == data


def test_multiple_messages_survive_stream_splitting():
    packets = [{'event': 'hello', 'backend': 'Qt ScreenCapture'},
               {'event': 'status', 'message': 'Zahajuji nahrávání úseku'},
               {'event': 'saved', 'path': r'C:\Nahrávky\střih.gif'}]
    combined = b''.join(encode_packet(p) for p in packets)
    # QProcess can deliver partial buffers. The parent reassembles on newlines.
    buffer = bytearray()
    got = []
    for part in [combined[:13], combined[13:29], combined[29:58], combined[58:]]:
        buffer.extend(part)
        while b'\n' in buffer:
            line, _, rest = buffer.partition(b'\n')
            buffer = bytearray(rest)
            got.append(decode_packet(line))
    assert got == packets
    assert not buffer


def test_malformed_message_is_rejected():
    with pytest.raises(UnicodeDecodeError):
        decode_packet('Připravuji snímek'.encode('cp1250'))
    with pytest.raises(ValueError):
        decode_packet(b'[1, 2, 3]')


def test_windows_legacy_stdout_codepage_does_not_corrupt_protocol():
    """Force cp1250 even on Linux, as a real Windows child process may use it."""
    root = Path(__file__).resolve().parent.parent
    code = """from capture_ipc import encode_packet
import sys
sys.stdout.buffer.write(encode_packet({'event': 'status', 'message': 'Připravuji nahrávání obrazovky – čekám na snímek'}))
sys.stdout.buffer.flush()
"""
    env = dict(os.environ, PYTHONIOENCODING='cp1250')
    proc = subprocess.run([sys.executable, '-u', '-c', code], cwd=root,
                          env=env, capture_output=True, check=True, timeout=10)
    assert decode_packet(proc.stdout)['message'] == 'Připravuji nahrávání obrazovky – čekám na snímek'
    assert all(x < 128 for x in proc.stdout)
