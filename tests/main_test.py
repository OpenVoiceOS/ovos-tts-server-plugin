# pylint: disable=missing-docstring,redefined-outer-name,protected-access
from unittest.mock import MagicMock, mock_open, patch

import pytest
from ovos_utils.log import LOG
from requests.exceptions import RequestException

from ovos_tts_plugin_server import PUBLIC_TTS_SERVERS, OVOSServerTTS, RemoteTTSException


@pytest.fixture
def tts_instance() -> OVOSServerTTS:
    return OVOSServerTTS()


@pytest.fixture
def tts_instance_factory():
    def create_instance(config):
        return OVOSServerTTS(config=config)

    return create_instance


def test_initialization(tts_instance):
    assert tts_instance.audio_ext == "wav"
    assert tts_instance.validator is not None
    assert tts_instance.log is LOG
    assert tts_instance.host is None
    assert tts_instance.v2 is True
    assert tts_instance.verify_ssl is True


def test_host_property(tts_instance, tts_instance_factory):
    # Default behavior - No host set
    assert tts_instance.host is None

    # Custom host set
    custom_host = "https://customhost.com"
    custom_tts_instance = tts_instance_factory({"host": custom_host})
    assert tts_instance.host != custom_tts_instance.host
    assert custom_tts_instance.host == [custom_host]

def test_tts_timeout_property(tts_instance):
    # Default behavior - No timeout set
    assert tts_instance.tts_timeout == 5

    # Custom timeout set
    custom_timeout = 10
    tts_instance.config["tts_timeout"] = custom_timeout
    assert tts_instance.tts_timeout == custom_timeout

@pytest.mark.parametrize("host,expected", [(None, True), ("https://customhost.com", False)])
def test_v2_property(tts_instance, host, expected):
    tts_instance.config["host"] = host
    assert tts_instance.v2 is expected


def test_verify_ssl_property(tts_instance):
    # Default behavior - SSL verification enabled
    assert tts_instance.verify_ssl is True

    # SSL verification explicitly disabled
    tts_instance.config["verify_ssl"] = False
    assert tts_instance.verify_ssl is False

    # SSL verification explicitly enabled
    tts_instance.config["verify_ssl"] = True
    assert tts_instance.verify_ssl is True


@patch("ovos_tts_plugin_server.OVOSServerTTS._fetch_audio_data", return_value=b"audio data")
@patch("ovos_tts_plugin_server.OVOSServerTTS._write_audio_file")
def test_get_tts(mock_write_audio, mock_fetch_audio, tts_instance):
    sentence = "test sentence"
    wav_file = "test.wav"
    result = tts_instance.get_tts(sentence, wav_file)

    mock_fetch_audio.assert_called_once()
    mock_write_audio.assert_called_once_with(wav_file, b"audio data")
    assert result[0] == wav_file


@patch("ovos_tts_plugin_server.requests.get")
def test_fetch_audio_data_success(mock_get, tts_instance):
    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.content = b"audio data"
    mock_get.return_value = mock_response

    sentence = "test sentence"
    servers = tts_instance.public_servers
    data = tts_instance._fetch_audio_data({}, sentence, servers)

    assert data == b"audio data"
    mock_get.assert_called()


@patch("ovos_tts_plugin_server.requests.get")
def test_fetch_audio_data_failure(mock_get, tts_instance):
    mock_response = MagicMock()
    mock_response.ok = False
    mock_get.return_value = mock_response

    sentence = "test sentence"
    servers = tts_instance.public_servers

    with pytest.raises(RemoteTTSException):
        tts_instance._fetch_audio_data({}, sentence, servers)

    assert mock_get.call_count == len(servers)  # Ensure all servers are tried


@patch("ovos_tts_plugin_server.requests.get", side_effect=RequestException)
def test_fetch_audio_data_exception(mock_get, tts_instance):
    sentence = "test sentence"
    servers = tts_instance.public_servers

    with pytest.raises(RemoteTTSException):
        tts_instance._fetch_audio_data({}, sentence, servers)

    assert mock_get.call_count == len(servers)  # Ensure all servers are tried


@patch("ovos_utils.log.LOG.warning")
def test_logged_warning(mock_log_warning, tts_instance_factory):
    # Create an instance with the specific configuration using the factory fixture
    tts_instance_factory({"verify_ssl": False})

    # Assertions to check the behavior and logging
    assert mock_log_warning.call_count == 1
    assert mock_log_warning.call_args[0][0] == (
        "SSL verification disabled, this is not secure and should"
        "only be used for test systems! Please set up a valid certificate!"
    )


def test_write_audio_file_success(tts_instance):
    mock_data = b"test audio data"
    mock_file_path = "test.wav"

    # Patch the built-in open function
    with patch("builtins.open", mock_open()) as mocked_file:
        tts_instance._write_audio_file(mock_file_path, mock_data)

        # Check if open was called correctly
        mocked_file.assert_called_with(file=mock_file_path, mode="wb")

        # Check if the correct data was written to the file
        mocked_file.return_value.write.assert_called_with(mock_data)


def test_validator(tts_instance):
    assert tts_instance.validator.validate_lang() is None
    assert tts_instance.validator.validate_connection() is None
    assert tts_instance.validator.get_tts_class() == OVOSServerTTS


@patch("ovos_tts_plugin_server.OVOSServerTTS._fetch_audio_data", return_value=b"audio data")
@patch("ovos_tts_plugin_server.OVOSServerTTS._write_audio_file")
def test_get_tts_param_change(_, fetch_audio_data, tts_instance):
    tts_instance.get_tts(sentence="test", wav_file="test.wav", lang="en-us", voice="default")
    fetch_audio_data.assert_called_with({"lang": "en-us"}, "test", PUBLIC_TTS_SERVERS)
    fetch_audio_data.reset_mock()

    tts_instance.get_tts(sentence="test", wav_file="test.wav", lang="en-us")
    fetch_audio_data.assert_called_with({"lang": "en-us"}, "test", PUBLIC_TTS_SERVERS)
    fetch_audio_data.reset_mock()

    tts_instance.get_tts(sentence="test", wav_file="test.wav", lang="en-us", voice="apope-low")
    fetch_audio_data.assert_called_with({"lang": "en-us", "voice": "apope-low"}, "test", PUBLIC_TTS_SERVERS)


@patch("ovos_tts_plugin_server.OVOSServerTTS._fetch_audio_data", return_value=b"audio data")
@patch("ovos_tts_plugin_server.OVOSServerTTS._write_audio_file")
def test_get_tts_server_lists(_, fetch_audio_data, tts_instance_factory):
    # Default behavior - No host set
    tts_instance = tts_instance_factory(config={})
    tts_instance.get_tts("test", "test.wav")
    fetch_audio_data.assert_called_with({"lang": "en-us"}, "test", tts_instance.public_servers)
    fetch_audio_data.reset_mock()
    # Custom host set
    custom_host = "https://customhost.com"
    tts_instance = tts_instance_factory(config={"host": custom_host})
    tts_instance.get_tts("test", "test.wav")
    fetch_audio_data.assert_called_with({"lang": "en-us"}, "test", [custom_host])
    fetch_audio_data.reset_mock()
    # Multiple hosts set
    custom_hosts = ["https://customhost1.com", "https://customhost2.com"]
    tts_instance = tts_instance_factory(config={"host": custom_hosts})
    tts_instance.get_tts("test", "test.wav")
    # Ensure custom list is NOT shuffled
    i = 0
    for host in custom_hosts:
        assert custom_hosts[i] == tts_instance.host[i]
        i += 1
    fetch_audio_data.assert_called_with({"lang": "en-us"}, "test", custom_hosts)


@patch("requests.get")
@patch("ovos_tts_plugin_server.OVOSServerTTS._write_audio_file")
def test_v2_property_passing(_, mock_requests, tts_instance_factory):
    # Default behavior
    tts_instance = tts_instance_factory({})
    assert tts_instance.v2 is True

    # Custom host set
    tts_instance = tts_instance_factory(config={"v2": False, "host": "https://customhost.com"})
    assert tts_instance.v2 is False
    tts_instance.get_tts("test", "test.wav")
    mock_requests.assert_called_with(
        url="https://customhost.com/synthesize/test",
        params={"lang": "en-us"},
        verify=True,
        timeout=5,
    )
