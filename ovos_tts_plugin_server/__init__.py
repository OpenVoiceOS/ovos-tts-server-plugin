"""OpenVoiceOS companion plugin for OpenVoiceOS TTS Server."""
import io
import random
import wave

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
    def host(self) -> Optional[list]:
        """If using a custom server, set the host here, otherwise it defaults to public servers."""
        hosts = self.config.get("host")
        if hosts and not isinstance(hosts, list):
            hosts = [hosts]
        return hosts

    @property
    def v2(self) -> bool:
        """default to v2"""
        return self.config.get("v2", True)

    @property
    def verify_ssl(self) -> bool:
        """Whether or not to verify SSL certificates when connecting to the server. Defaults to True."""
        return self.config.get("verify_ssl", True)

    @property
    def tts_timeout(self) -> int:
        """Timeout for the TTS server. Defaults to 5 seconds."""
        return self.config.get("tts_timeout", 5)

    @property
    def server_type(self) -> str:
        """Which server API to speak to.

        ``ovos`` (default) talks to a native ovos-tts-server. Any other value
        turns this plugin into an adapter for a third-party TTS API so it can
        target any compatible server:
        - ``openai``: OpenAI ``/v1/audio/speech`` (also covers kokoro-fastapi,
          LocalAI and other OpenAI-compatible servers via a custom ``host``).
        - ``elevenlabs``: ElevenLabs ``/v1/text-to-speech/{voice_id}``.
        """
        return self.config.get("server_type", "ovos")

    @property
    def api_key(self) -> Optional[str]:
        """API key for vendor server types (Bearer / xi-api-key). Optional."""
        return self.config.get("api_key")

    def get_tts(
            self,
            sentence,
            wav_file,
            lang: Optional[str] = None,
            voice: Optional[str] = None,
    ) -> Tuple[Any, None]:
        """Fetch TTS audio from the configured server.
        Language and voice can be overridden, otherwise defaults to config."""
        lang = lang or self.lang
        voice = voice or self.voice
        if self.server_type == "ovos":
            params: Dict[str, Optional[str]] = {"lang": lang, "voice": voice}
            if not voice or voice == "default":
                params.pop("voice")
            if self.host:
                servers = self.host
            else:
                random.shuffle(self.public_servers)
                servers = self.public_servers
            data: bytes = self._fetch_audio_data(params, sentence, servers)
        else:
            if not self.host:
                raise RemoteTTSException(
                    f"server_type={self.server_type!r} requires an explicit 'host'")
            data = self._fetch_vendor_audio(sentence, voice, lang, self.host)
        self._write_audio_file(wav_file, data)
        return wav_file, None

    def _fetch_vendor_audio(self, sentence: str, voice: Optional[str],
                            lang: Optional[str], servers: list) -> bytes:
        """Synthesize via a third-party TTS API, returning WAV bytes."""
        for url in servers:
            try:
                if self.server_type == "openai":
                    data = self._synth_openai(url, sentence, voice)
                elif self.server_type == "elevenlabs":
                    data = self._synth_elevenlabs(url, sentence, voice)
                else:
                    raise RemoteTTSException(f"unknown server_type {self.server_type!r}")
                if data:
                    return data
            except RemoteTTSException:
                raise
            except Exception as err:  # pylint: disable=broad-except
                self.log.error(f"Failed to get audio from {url}: {err}")
                continue
        raise RemoteTTSException(f"All {self.server_type} TTS servers are down!")

    def _synth_openai(self, url: str, sentence: str, voice: Optional[str]) -> Optional[bytes]:
        """OpenAI-compatible POST /v1/audio/speech (returns WAV)."""
        endpoint = url.rstrip("/")
        if not endpoint.endswith("/v1"):
            endpoint += "/v1"
        endpoint += "/audio/speech"
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        body = {
            "model": self.config.get("model", "tts-1"),
            "input": sentence,
            "voice": voice if voice and voice != "default" else "alloy",
            "response_format": "wav",
        }
        r = requests.post(endpoint, json=body, headers=headers,
                          timeout=self.tts_timeout, verify=self.verify_ssl)
        if r.ok:
            return r.content
        self.log.error(f"OpenAI-compatible TTS error from {endpoint}: {r.text}")
        return None

    def _synth_elevenlabs(self, url: str, sentence: str, voice: Optional[str]) -> Optional[bytes]:
        """ElevenLabs POST /v1/text-to-speech/{voice_id}; PCM wrapped to WAV."""
        if not voice or voice == "default":
            raise RemoteTTSException("elevenlabs server_type requires a 'voice' (voice_id)")
        endpoint = f"{url.rstrip('/')}/v1/text-to-speech/{voice}"
        headers = {"Accept": "audio/wav"}
        if self.api_key:
            headers["xi-api-key"] = self.api_key
        body = {"text": sentence,
                "model_id": self.config.get("model", "eleven_multilingual_v2")}
        # request raw PCM and wrap it in a WAV container (audio_ext is "wav")
        r = requests.post(endpoint, json=body, headers=headers,
                          params={"output_format": "pcm_22050"},
                          timeout=self.tts_timeout, verify=self.verify_ssl)
        if not r.ok:
            self.log.error(f"ElevenLabs TTS error from {endpoint}: {r.text}")
            return None
        return self._pcm_to_wav(r.content, sample_rate=22050)

    @staticmethod
    def _pcm_to_wav(pcm: bytes, sample_rate: int = 22050) -> bytes:
        """Wrap raw 16-bit mono PCM bytes in a WAV container."""
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(pcm)
        return buf.getvalue()

    def _write_audio_file(self, wav_file: str, data: bytes) -> None:
        with open(file=wav_file, mode="wb") as f:
            f.write(data)

    def _request_audio(self, base_url: str, params: dict, sentence: str, v2: bool) -> Optional[bytes]:
        """Request audio from a single server using the v2 or legacy endpoint.

        Returns the audio bytes on success, or None if the server did not
        return a usable response (so the caller can try a fallback/next server).
        """
        if v2:
            url = f"{base_url}/v2/synthesize"
            params = {**params, "utterance": sentence}
        else:
            url = f"{base_url}/synthesize/{sentence}"
        self.log.debug(f"Chosen TTS server {url}")
        try:
            r: requests.Response = requests.get(url=url, params=params, verify=self.verify_ssl,
                                                timeout=self.tts_timeout)
            if r.ok:
                return r.content
            self.log.error(f"Failed to get audio, response from {url}: {r.text}")
        except Exception as err:  # pylint: disable=broad-except
            self.log.error(f"Failed to get audio from {url}: {err}")
        return None

    def _fetch_audio_data(self, params: dict, sentence: str, servers: list) -> bytes:
        """Get audio bytes from servers.

        When configured for v2 (the default) but a server does not serve the
        v2 endpoint, fall back to the legacy endpoint on that same server
        before moving on, so the plugin works against both server generations.
        """
        for url in servers:
            data = self._request_audio(url, params, sentence, self.v2)
            if data is not None:
                return data
            if self.v2:
                # server may be a legacy server without the v2 endpoint
                data = self._request_audio(url, params, sentence, v2=False)
                if data is not None:
                    return data
        raise RemoteTTSException("All OVOS TTS servers are down!")

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
