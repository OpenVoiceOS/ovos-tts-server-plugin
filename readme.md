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
    "verify_ssl": "true"
 }
```

If using a Piper TTS server since version 0.0.1a9, you can use the
`/v2` endpoint to take advantage of newer features. Be sure to include that
in the `host` value if you'd like to use it. Example: `https://tts.smartgic.io/piper/v2`

Please note that while you can set `verify_ssl` to `false` to disable SSL
verification, this is not recommended and should only be used for testing
purposes. Consider using a private CA or certificates signed using
[Let's Encrypt](https://letsencrypt.org/) instead.
