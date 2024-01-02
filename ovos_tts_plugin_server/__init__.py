"""OpenVoiceOS companion plugin for OpenVoiceOS TTS Server."""
import random
from typing import Any, Dict, List, Optional, Tuple

import requests
from ovos_plugin_manager.templates.tts import TTS, RemoteTTSException, TTSValidator
from ovos_utils.log import LOG

PUBLIC_TTS_SERVERS = [
    "https://pipertts.ziggyai.online",
    "https://tts.smartgic.io/piper",
]


class OVOSServerTTS(TTS):
    """Interface to OVOS TTS server"""

    public_servers: List[str] = PUBLIC_TTS_SERVERS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, audio_ext="wav", validator=OVOSServerTTSValidator(self))
        self.log = LOG
        if not self.verify_ssl:
            self.log.warning(
                "SSL verification disabled, this is not secure and should"
                "only be used for test systems! Please set up a valid certificate!"
            )

    @property
    def host(self) -> Optional[str]:
        """If using a custom server, set the host here, otherwise it defaults to public servers."""
        return self.config.get("host", None)

    @property
    def v2(self) -> bool:
        """If using default public servers, default to v2, else v1"""
        return self.config.get("v2", self.host is None)

    @property
    def verify_ssl(self) -> bool:
        """Whether or not to verify SSL certificates when connecting to the server. Defaults to True."""
        return self.config.get("verify_ssl", True)

    def get_tts(
        self,
        sentence,
        wav_file,
        lang: Optional[str] = None,
        voice: Optional[str] = None,
    ) -> Tuple[Any, None]:
        """Fetch TTS audio using OVOS TTS server.
        Language and voice can be overridden, otherwise defaults to config."""
        params: Dict[str, Optional[str]] = {
            "lang": lang or self.lang,
            "voice": voice or self.voice,
        }
        if not voice or voice == "default":
            params.pop("voice")
        if self.host:
            if isinstance(self.host, str):
                servers: List[str] = [self.host]
            else:
                servers = self.host
        else:
            servers = self.public_servers
        data: bytes = self._fetch_audio_data(params, sentence, servers)
        self._write_audio_file(wav_file, data)
        return wav_file, None

    def _write_audio_file(self, wav_file: str, data: bytes) -> None:
        with open(file=wav_file, mode="wb") as f:
            f.write(data)

    def _fetch_audio_data(self, params: dict, sentence: str, servers: list) -> bytes:
        """Get audio bytes from servers."""
        random.shuffle(servers)  # Spread the load among all public servers
        for url in servers:
            try:
                if self.v2:
                    url = f"{url}/v2/synthesize"
                    params["utterance"] = sentence
                else:
                    url = f"{url}/synthesize/{sentence}"
                r: requests.Response = requests.get(url=url, params=params, verify=self.verify_ssl, timeout=30)
                if r.ok:
                    return r.content
                self.log.error(f"Failed to get audio, response from {url}: {r.text}")
            except Exception as err:  # pylint: disable=broad-except
                self.log.error(f"Failed to get audio from {url}: {err}")
                continue
        raise RemoteTTSException("All OVOS TTS servers are down!")


class OVOSServerTTSValidator(TTSValidator):
    """Validate settings for OVOS TTS server plugin."""

    def __init__(self, tts) -> None:  # pylint: disable=useless-parent-delegation
        super(OVOSServerTTSValidator, self).__init__(tts)

    def validate_lang(self) -> None:
        """Validate language setting."""
        return

    def validate_connection(self) -> None:
        """Validate connection to server."""
        return

    def get_tts_class(self):
        """Return TTS class."""
        return OVOSServerTTS


OVOSServerTTSConfig: Dict[Any, Any] = {}
