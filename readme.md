## Description

OpenVoiceOS companion plugin for [OpenVoiceOS TTS Server](https://github.com/OpenVoiceOS/ovos-tts-server)

## Install

```bash
pip install ovos-tts-plugin-server
```

## Configuration

```json
  "tts": {
    "module": "ovos-tts-plugin-server",
    "ovos-tts-plugin-server": {"host": "https://0.0.0.0:9666"},
    "host": "https://tts.smartgic.io/piper",
    "v2": true,
    "verify_ssl": true
 }
```

### As of ovos-tts-server 0.0.3a10

If using a TTS plugin with v2, you can use the `/v2` config option
to take advantage of newer features. There is no need to change
the `host`, however. It would always look something like: `https://tts.smartgic.io/piper`
regardless of the `v2` value.

### Security warning

Please note that while you can set `verify_ssl` to `false` to disable SSL
verification, this is not recommended and should only be used for testing
purposes. Consider using a private CA or certificates signed using
[Let's Encrypt](https://letsencrypt.org/) instead.
