import requests
from ovos_plugin_manager.templates.tts import TTS, TTSValidator, RemoteTTSException


class OVOSServerTTS(TTS):
    public_servers = (
        "https://mimic3.ziggyai.online/",
        "https://tts.smartgic.io/mimic3/"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, audio_ext="wav",
                         validator=OVOSServerTTSValidator(self))
        self.host = self.config.get("host") or "http://0.0.0.0:9666"

    def get_tts(self, sentence, wav_file, lang=None, voice=None):
        lang = lang or self.lang
        voice = voice or self.voice
        params = {"lang": lang, "voice": voice}
        if not voice or voice == "default":
            params.pop("voice")
        if self.host:
            data = requests.get(f"{self.host}/synthesize/{sentence}",
                                params=params).content
        else:
            data = self._get_from_public_servers(params, sentence)
        with open(wav_file, "wb") as f:
            f.write(data)
        return wav_file, None

    def _get_from_public_servers(self, params: dict, sentence: str):
        for url in self.public_servers:
            try:
                r = requests.get(f'{url}/synthesize/{sentence}',
                                 params=params)
                if r.ok:
                    return r.content
            except:
                continue
        raise RemoteTTSException(f"All OVOS TTS public servers are down!")


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
