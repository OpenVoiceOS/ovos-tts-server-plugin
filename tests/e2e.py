# pylint: disable=missing-docstring,redefined-outer-name,protected-access
import os

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ovos_tts_plugin_server import OVOSServerTTS


def requests_retry_session(retries=3, backoff_factor=0.3, status_forcelist=(500, 502, 503, 504)):
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def test_tts_plugin_e2e():
    tts_instance = OVOSServerTTS(config={"host": "http://localhost:9666"})
    tts_instance.get_tts(sentence="Hello%20world", wav_file="test.wav")
    assert os.path.exists(path="test.wav")
    assert os.path.getsize(filename="test.wav") > 0
    os.remove("test.wav")
