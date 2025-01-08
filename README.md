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

## Using a list of TTS servers

Similar to the use of several alternative STT servers different TTS servers can be specified in a list to increase reliability. The servers can be located in the local network or on the Internet. The following restrictions apply: The servers can only be addressed via the ```ovos-tts-plugin-server``` module (e.g. Piper_TTS) and the default voice and language of the server is used (mostly English). This can result in the text converted to speech being spoken in the intonation of a different language.

### Configuration example
Example for using two local servers and two community servers. The servers are addressed one after the other. If one does not respond (within the timeout period), the next one is contacted.
```
"tts": {
    "module": "ovos-tts-plugin-server",
    "ovos-tts-plugin-server": {
        "host": [
            "http://192.168.178.21:8089",
            "http://192.168.178.20:8089",
            "https://tts.smartgic.io/piper",
            "https://pipertts.ziggyai.online"
        ]
    }
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
