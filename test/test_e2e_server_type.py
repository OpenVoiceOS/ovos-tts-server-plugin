# pylint: disable=missing-docstring,redefined-outer-name,protected-access
"""End-to-end tests for the server_type adapter over a real socket.

The plugin *is* the client, so these tests run the real plugin (real
``requests`` HTTP, real WAV decoding) against a real local server that speaks
the vendor wire format. No mocking, no external network.
"""
import io
import json
import os
import threading
import wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from ovos_tts_plugin_server import OVOSServerTTS


def _wav_bytes(rate=22050, frames=160) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(b"\x10\x00" * frames)
    return buf.getvalue()


class _VendorHandler(BaseHTTPRequestHandler):
    def log_message(self, *_):  # silence
        pass

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        self.rfile.read(length)
        if self.path == "/v1/audio/speech":  # OpenAI
            body = _wav_bytes()
        elif self.path.startswith("/v1/text-to-speech/"):  # ElevenLabs (raw PCM)
            body = b"\x10\x00" * 160
        else:
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


@pytest.fixture(scope="module")
def vendor_server():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), _VendorHandler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


def test_openai_adapter_end_to_end(vendor_server, tmp_path):
    tts = OVOSServerTTS(config={"server_type": "openai", "host": vendor_server,
                                "api_key": "sk-test"})
    out = str(tmp_path / "openai.wav")
    tts.get_tts("Hello world", out, voice="nova")
    assert os.path.getsize(out) > 0
    with wave.open(out, "rb") as wf:
        assert wf.getnframes() > 0


def test_elevenlabs_adapter_end_to_end(vendor_server, tmp_path):
    tts = OVOSServerTTS(config={"server_type": "elevenlabs", "host": vendor_server,
                                "api_key": "xi-test"})
    out = str(tmp_path / "11labs.wav")
    tts.get_tts("Hello world", out, voice="Rachel")
    assert os.path.getsize(out) > 0
    with wave.open(out, "rb") as wf:
        assert wf.getframerate() == 22050
        assert wf.getnframes() > 0
