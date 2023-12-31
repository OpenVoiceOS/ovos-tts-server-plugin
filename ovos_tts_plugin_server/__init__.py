from typing import Optional
import requests
import random
from ovos_plugin_manager.templates.tts import TTS, TTSValidator, RemoteTTSException


class OVOSServerTTS(TTS):
    public_servers = [
        "https://pipertts.ziggyai.online",
        "https://tts.smartgic.io/piper"
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, audio_ext="wav",
                         validator=OVOSServerTTSValidator(self))
        if not self.verify_ssl:
            self.log.warning("SSL verification disabled, this is not secure and should"
                             "only be used for test systems! Please set up a valid certificate!")

    @property
    def host(self) -> Optional[str]:
        return self.config.get("host", None)

    @property
    def v2(self) -> bool:
        """If using default public servers, default to v2, else v1"""
        return self.config.get("v2", self.host is None)

    @property
    def verify_ssl(self) -> bool:
        return self.config.get("verify_ssl", True)

    def get_tts(self, sentence, wav_file, lang=None, voice=None):
        lang = lang or self.lang
        voice = voice or self.voice
        params = {"lang": lang, "voice": voice}
        if not voice or voice == "default":
            params.pop("voice")
        if self.host:
            if isinstance(self.host, str):
                servers = [self.host]
            else:
                servers = self.host
        else:
            servers = self.public_servers 
        data = self._get_from_servers(params, sentence, servers)
        with open(wav_file, "wb") as f:
            f.write(data)
        return wav_file, None

    def _get_from_servers(self, params: dict, sentence: str, servers: list):
        random.shuffle(servers)  # Spread the load among all public servers
        for url in servers:
            try:
                if self.v2:
                    url = f'{url}/v2/synthesize'
                    params["utterance"] = sentence
                else:
                    url = f'{url}/synthesize/{sentence}'
                r = requests.get(url, params=params, verify=self.verify_ssl)
                if r.ok:
                    return r.content
            except:
                continue
        raise RemoteTTSException(f"All OVOS TTS servers are down!")


class OVOSServerTTSValidator(TTSValidator):
    def __init__(self, tts):
        super(OVOSServerTTSValidator, self).__init__(tts)

    def validate_lang(self):
        pass

    def validate_connection(self):
        pass

    def get_tts_class(self):
        return OVOSServerTTS


OVOSServerTTSConfig = {}
