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
    "ovos-tts-plugin-server": {
        "host": "https://tts.smartgic.io/piper",
        "v2": true,
        "verify_ssl": true,
        "tts_timeout": 5
     }
 } 
```

- host: the url of the tts server. `/synthesize` will be appended to it in the code
- v2: use the v2 api, if available
- verify_ssl: verify the ssl certificate of the server. If you use a self-signed certificate, you can set this to false, [but it is not recommended](#security-warning)
- tts_timeout: timeout for the request to the server. Defaults to 5 seconds.

### Universal adapter (`server_type`)

By default the plugin talks to a native `ovos-tts-server` (`server_type: "ovos"`).
Set `server_type` to target any other compatible TTS API — the plugin becomes a
universal adapter and can point at a vendor service or any self-hosted
OpenAI-compatible server:

```json
  "tts": {
    "module": "ovos-tts-plugin-server",
    "ovos-tts-plugin-server": {
        "server_type": "openai",
        "host": "https://api.openai.com",
        "api_key": "sk-...",
        "voice": "nova",
        "model": "tts-1"
     }
 }
```

| `server_type` | Endpoint used | `host` example | Notes |
|---|---|---|---|
| `ovos` (default) | `/v2/synthesize` | `https://tts.smartgic.io/piper` | native ovos-tts-server |
| `openai` | `/v1/audio/speech` | `https://api.openai.com` | also covers any OpenAI-compatible server — point `host` at a self-hosted **kokoro-fastapi** or **LocalAI** |
| `elevenlabs` | `/v1/text-to-speech/{voice_id}` | `https://api.elevenlabs.io` | `voice` is the ElevenLabs `voice_id` |

`api_key` is sent as `Authorization: Bearer` (openai) or `xi-api-key`
(elevenlabs). For vendor server types an explicit `host` is required (the public
OVOS server list is only used by `server_type: "ovos"`).

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
