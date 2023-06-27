import requests
from ovos_plugin_manager.templates.tts import TTS, TTSValidator


class OVOSServerTTS(TTS):
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
        data = requests.get(f"{self.host}/synthesize/{sentence}",
                            params=params).content
        with open(wav_file, "wb") as f:
            f.write(data)
        return wav_file, None


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
