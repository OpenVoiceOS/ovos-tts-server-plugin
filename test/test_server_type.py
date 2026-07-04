# pylint: disable=missing-docstring,redefined-outer-name,protected-access
"""Unit tests for the server_type universal adapter (mocked HTTP)."""
import io
import wave
from unittest.mock import patch, MagicMock

import pytest

from ovos_tts_plugin_server import OVOSServerTTS, RemoteTTSException


def _wav_bytes() -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(22050)
        wf.writeframes(b"\x00\x00" * 100)
    return buf.getvalue()


def _ok(content: bytes) -> MagicMock:
    r = MagicMock()
    r.ok = True
    r.content = content
    return r


def test_default_server_type_is_ovos():
    assert OVOSServerTTS().server_type == "ovos"


def test_openai_request_shape(tmp_path):
    tts = OVOSServerTTS(config={"server_type": "openai",
                                "host": "http://localhost:1234",
                                "api_key": "sk-test", "model": "tts-1"})
    with patch("ovos_tts_plugin_server.requests.post", return_value=_ok(_wav_bytes())) as post:
        out = str(tmp_path / "o.wav")
        tts.get_tts("hello world", out, voice="nova")
    args, kwargs = post.call_args
    assert args[0] == "http://localhost:1234/v1/audio/speech"
    assert kwargs["headers"]["Authorization"] == "Bearer sk-test"
    assert kwargs["json"]["input"] == "hello world"
    assert kwargs["json"]["voice"] == "nova"
    assert kwargs["json"]["response_format"] == "wav"
    assert wave.open(out, "rb").getnframes() == 100


def test_openai_appends_v1_only_once(tmp_path):
    tts = OVOSServerTTS(config={"server_type": "openai", "host": "http://localhost:1234/v1"})
    with patch("ovos_tts_plugin_server.requests.post", return_value=_ok(_wav_bytes())) as post:
        tts.get_tts("hi", str(tmp_path / "o.wav"))
    assert post.call_args.args[0] == "http://localhost:1234/v1/audio/speech"


def test_elevenlabs_request_shape(tmp_path):
    tts = OVOSServerTTS(config={"server_type": "elevenlabs",
                                "host": "http://localhost:1234", "api_key": "xi-test"})
    # ElevenLabs returns raw PCM; the adapter wraps it into a WAV container
    raw_pcm = b"\x01\x00" * 200
    with patch("ovos_tts_plugin_server.requests.post", return_value=_ok(raw_pcm)) as post:
        out = str(tmp_path / "o.wav")
        tts.get_tts("hello", out, voice="Rachel")
    args, kwargs = post.call_args
    assert args[0] == "http://localhost:1234/v1/text-to-speech/Rachel"
    assert kwargs["headers"]["xi-api-key"] == "xi-test"
    assert kwargs["params"]["output_format"] == "pcm_22050"
    with wave.open(out, "rb") as wf:
        assert wf.getframerate() == 22050
        assert wf.getnframes() == 200


def test_elevenlabs_requires_voice(tmp_path):
    tts = OVOSServerTTS(config={"server_type": "elevenlabs", "host": "http://localhost:1234"})
    with pytest.raises(RemoteTTSException):
        tts.get_tts("hello", str(tmp_path / "o.wav"))


def test_vendor_type_requires_host(tmp_path):
    tts = OVOSServerTTS(config={"server_type": "openai"})
    with pytest.raises(RemoteTTSException):
        tts.get_tts("hello", str(tmp_path / "o.wav"))


def test_unknown_server_type_raises(tmp_path):
    tts = OVOSServerTTS(config={"server_type": "bogus", "host": "http://localhost:1234"})
    with pytest.raises(RemoteTTSException):
        tts.get_tts("hello", str(tmp_path / "o.wav"))


def test_ovos_path_unchanged(tmp_path):
    """server_type=ovos still hits /v2/synthesize as before."""
    tts = OVOSServerTTS(config={"host": "http://localhost:1234", "v2": True})
    with patch("ovos_tts_plugin_server.requests.get", return_value=_ok(_wav_bytes())) as get:
        tts.get_tts("hello world", str(tmp_path / "o.wav"))
    assert get.call_args.kwargs["url"] == "http://localhost:1234/v2/synthesize"
