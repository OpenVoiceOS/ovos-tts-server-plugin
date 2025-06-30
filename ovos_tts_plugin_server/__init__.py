"""OpenVoiceOS companion plugin for OpenVoiceOS and OpenAI TTS Servers."""

import json
import random
import requests
from ovos_plugin_manager.templates.tts import TTS, RemoteTTSException, TTSValidator
from ovos_utils import classproperty
from ovos_utils.log import LOG
from typing import Any, Dict, List, Optional, Tuple

PUBLIC_TTS_SERVERS = ["https://pipertts.ziggyai.online", "https://tts.smartgic.io/piper"]


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
    def api(self) -> str:
        """Defaults to 'ovos' because of backwards compatibility."""
        return self.config.get("api", "ovos")

    @property
    def apikey(self) -> str:
        return self.config.get("apikey", None)

    @property
    def host(self) -> Optional[list]:
        """If using a custom server, set the host here, otherwise it defaults to public servers."""
        hosts = self.config.get("host")
        if hosts and not isinstance(hosts, list):
            hosts = [hosts]
        return hosts

    @property
    def model(self) -> str:
        return self.config.get("model", None)

    @property
    def tts_timeout(self) -> int:
        """Timeout for the TTS server. Defaults to 5 seconds."""
        return self.config.get("tts_timeout", 5)

    @property
    def v2(self) -> bool:
        """default to v2"""
        return self.config.get("v2", True)

    @property
    def verify_ssl(self) -> bool:
        """Whether or not to verify SSL certificates when connecting to the server. Defaults to True."""
        return self.config.get("verify_ssl", True)

    @property
    def voice(self) -> str:
        return self.config.get("voice", None)

    def get_tts(
            self,
            sentence,
            wav_file,
            api: Optional[str] = None, 
            apikey: Optional[str] = None,
            lang: Optional[str] = None,
            model: Optional[str] = None,
            voice: Optional[str] = None
    ) -> Tuple[Any, None]:
        """Fetch TTS audio using a TTS server API. API defaults to OVOS TTS.
        Language, model and voice can be overridden, otherwise defaults to config."""
        params: Dict[str, Optional[str]] = {
            "lang": lang or self.lang,
            "model": model or self.model,
            "voice": voice or self.voice,
        }
        if not voice or voice == "default":
            params.pop("voice")
        if self.api == "ovos":
            params.pop("model") # we can't set it in ovos tts
            if self.host:
                servers = self.host
            else:
                random.shuffle(self.public_servers)
                servers = self.public_servers
            data: bytes = self._fetch_audio_data_ovos(params, sentence, servers)
        elif self.api == "openai":
            params.pop("lang") # we can't set it in openai
            if not model:
                params["model"] = "default"
            if not voice:
                params["voice"] = "nova"
            params["response_format"] = "wav"
            if self.host:
                servers = self.host
            else: # we use official OpenAI service (paid!)
                servers = "https://api.openai.com"
            data: bytes = self._fetch_audio_data_openai(params, sentence, servers, self.apikey)

        self._write_audio_file(wav_file, data)
        return wav_file, None

    def _write_audio_file(self, wav_file: str, data: bytes) -> None:
        with open(file=wav_file, mode="wb") as f:
            f.write(data)

    def _fetch_audio_data_ovos(self, params: dict, sentence: str, servers: list) -> bytes:
        """Get audio bytes from OVOS TTS servers."""
        for url in servers:
            try:
                if self.v2:
                    url = f"{url}/v2/synthesize"
                    params["utterance"] = sentence
                else:
                    url = f"{url}/synthesize/{sentence}"
                self.log.debug(f"Chosen OVOS TTS server {url}")
                r: requests.Response = requests.get(url=url, params=params, verify=self.verify_ssl,
                                                    timeout=self.tts_timeout)
                if r.ok:
                    return r.content
                self.log.error(f"Failed to get audio, response from {url}: {r.text}")
            except Exception as err:  # pylint: disable=broad-except
                self.log.error(f"Failed to get audio from {url}: {err}")
                continue
        raise RemoteTTSException("All OVOS TTS servers are down!")

    def _fetch_audio_data_openai(self, params: dict, sentence: str, servers: list, apikey: str) -> bytes:
        """Get audio bytes from OpenAI TTS servers.
        https://platform.openai.com/docs/api-reference/audio/createSpeech
        https://github.com/erew123/alltalk_tts/wiki/API-%E2%80%90-OpenAI-V1-Speech-Compatible-Endpoint
        """
        for url in servers:
            headers = {
                "Content-Type": "application/json"
            }
            if apikey:
                headers["Authorization"] = f"Bearer: {apikey}"
            try:
                url = f"{url}/v1/audio/speech"
                params["input"] = sentence
                data = json.dumps(params)
                self.log.debug(f"Chosen OpenAI TTS server {url}")
                self.log.debug(f"Request to OpenAI TTS server {data}")
                r: requests.Response = requests.post(url=url, headers=headers, data=data,
                                                    verify=self.verify_ssl,
                                                    timeout=self.tts_timeout)
                if r.ok:
                    return r.content
                self.log.error(f"Failed to get audio, response from {url}: {r.text}")
            except Exception as err:  # pylint: disable=broad-except
                self.log.error(f"Failed to get audio from {url}: {err}")
                continue
        raise RemoteTTSException("All OpenAI TTS servers are down!")

    @classproperty
    def available_languages(self) -> set:
        """Return languages supported by this TTS implementation in this state
        This property should be overridden by the derived class to advertise
        what languages that engine supports.
        Returns:
            set: supported languages
        """
        return set()  # TODO


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
