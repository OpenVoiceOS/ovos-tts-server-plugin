## Description

This plugin connects OpenVoiceOS to an [OpenVoiceOS TTS Server](https://github.com/OpenVoiceOS/ovos-tts-server) instance. It sends text to the server and returns the synthesized audio to OVOS.

## Install

```bash
pip install ovos-tts-plugin-server
```

## Configuration

```json
  "tts": {
    "module": "ovos-tts-plugin-server",
    "ovos-tts-plugin-server": {
        "host": "https://tts.smartgic.io/piper",
        "v2": true,
        "verify_ssl": true,
        "tts_timeout": 5
     }
 } 
```

- `host`: the URL of the TTS server. The plugin appends `/synthesize` to this URL.
- `v2`: use the v2 API, if the server offers it.
- `verify_ssl`: verify the server's SSL certificate. Set this to `false` for a self-signed certificate, but see the [security warning](#security-warning) before you do.
- `tts_timeout`: timeout, in seconds, for a request to the server. The default is 5 seconds.

### v2 API (ovos-tts-server 0.0.3a10 and later)

If the TTS server plugin supports v2, set `v2` to `true` to use the newer API. The `host` value stays the same either way. For example, it stays `https://tts.smartgic.io/piper` regardless of the `v2` setting.

### Security warning

You can set `verify_ssl` to `false` to disable SSL verification, but this is not recommended. Use it only for testing. For production, use a private CA or a certificate from [Let's Encrypt](https://letsencrypt.org/) instead.

## Related projects

- [OpenVoiceOS/ovos-tts-server](https://github.com/OpenVoiceOS/ovos-tts-server) — the TTS server this plugin talks to.
- [OpenVoiceOS/ovos-plugin-manager](https://github.com/OpenVoiceOS/ovos-plugin-manager) — loads and configures this plugin inside OVOS.

## License

Apache-2.0
