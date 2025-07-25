# 🎵 YouTube DL Add-on for Home Assistant

## ❗NOTE: The main download/extraction part is already covered by official [media_extractor](https://www.home-assistant.io/integrations/media_extractor)

This is a lightweight Flask-based add-on for Home Assistant using [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) 

- ✅ Download **YouTube videos** as `.mp4`
- ✅ Download **YouTube audio** as `.mp3`
- ✅ Stream **YouTube audio directly to media_player** (e.g., Google Nest Mini)

---

## 📦 Features

| Feature          | Method           | Output                |
|------------------|------------------|------------------------|
| `video` download | REST             | Saved `.mp4` in `/media` folder |
| `audio` download | REST             | Saved `.mp3` in `/media` folder |
| `stream`         | Shell + API call | Plays on selected `media_player` |

---

## 🔌 Home Assistant Integration

### 🔁 Download via `rest_command`

Used for both `video` and `audio` downloads:

```yaml
rest_command:
  yt_dlp_download:
    url: "http://192.168.X.X:5903/download"  # add-on port
    method: POST
    content_type: "application/json"
    payload: '{"download_url": "{{ download_url }}", "media_type": "{{ media_type }}"}'
```
- download_url: full YouTube link
- media_type: either "video" or "audio"

📂 Downloaded files are saved to /media/ytdowns/video/ or /media/ytdowns/audio/ accordingly.



### 📡 Streaming via `shell_command`

Since rest_command does not support capturing response, streaming is handled via shell_command:

```yaml
shell_command:
  get_youtube_stream: /bin/bash -c "/config/youtube_dl/stream.sh {{url}} {{player}}"
```
- url: YouTube video URL
- player: media_player entity (e.g., media_player.living_room_speaker)


🔀 stream.sh Example
```
#!/bin/bash
HA_URL="https://192.168.X.X:8123" 
TOKEN="eyJ....."  # Replace with a valid Long-Lived Access Token

STREAM=$(curl -s -X POST http://<add-on-ip>:5903/download \
  -H "Content-Type: application/json" \
  -d "{\"download_url\": \"$1\", \"media_type\": \"stream\"}" | jq -r '.stream_url')

if [ "$STREAM" = "null" ] || [ -z "$STREAM" ]; then
  echo "Failed to get stream URL"
  exit 1
fi

curl -k -X POST "$HA_URL/api/services/media_player/play_media" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "entity_id": "'"$2"'",
    "media_content_id": "'"$STREAM"'",
    "media_content_type": "audio/mp4"
  }'


```
## 🎛️ Sample Lovelace Options

```
type: entities
entities:
  - entity: input_text.youtube_dl_url
    name: URL
  - type: custom:template-entity-row
    entity: input_boolean.ytdlptype
    name: |
      {{ 'Video' if is_state('input_boolean.ytdlptype', 'on') else 'Audio' }}
    icon: >
      {{ 'mdi:movie-open' if is_state('input_boolean.ytdlptype', 'on') else
      'mdi:music-note' }}
    toggle: true
    style: |
      :host {
        --state-icon-color: var(--primary-text-color);
        --state-icon-active-color: var(--primary-text-color);
      }
  - type: button
    entity: script.ytdlp
    tap_action:
      action: call-service
      service: script.ytdlp
    name: " "
    icon: none
title: " YT MP3 Downloader"
```
```
#script.ytdlp
alias: YT-DLP Download
sequence:
  - data:
      download_url: "{{ states('input_text.youtube_dl_url') }}"
      media_type: "{{ 'video' if is_state('input_boolean.ytdlptype', 'on') else 'audio' }}"
    action: rest_command.yt_dlp_download
mode: single
```
![image](https://github.com/user-attachments/assets/71f1a3dd-8767-42a9-a42b-02891e2a34d4)
![image](https://github.com/user-attachments/assets/0c0b2e90-0775-4ffc-9c34-e45051bc5c3a)

```
type: entities
entities:
  - entity: input_text.youtube_dl_stream
    name: URL
  - entity: input_select.youtube_stream_player
    name: "Player:"
    icon: mdi:play
  - type: button
    entity: script.stream_youtube_to_speaker
    tap_action:
      action: call-service
      service: script.stream_youtube_to_speaker
    name: " "
    icon: none
title: " YT Streamer"
```
```
#script.stream_youtube_to_speaker
alias: Stream YouTube to Speaker
sequence:
  - variables:
      url: "{{ states('input_text.youtube_dl_stream') }}"
      player: "{{ states('input_select.youtube_stream_player') }}"
  - data:
      url: "{{ url }}"
      player: "{{ player }}"
    action: shell_command.get_youtube_stream
mode: single

```
![image](https://github.com/user-attachments/assets/9b17d42a-5b41-4771-93e2-42d27d048a0c)


## 🧪 Sample API Payloads

✅ Download Audio:

```json
{
  "download_url": "https://www.youtube.com/watch?v=d......",
  "media_type": "audio"
}
```
✅ Stream Audio:
Used in stream.sh, returns direct audio URL:

```json
{
  "download_url": "https://www.youtube.com/watch?v=d......",
  "media_type": "stream"
}
```
🛡️ Security Tip
Use HTTPS and a Home Assistant Long-Lived Access Token when calling the media_player/play_media API.

🙌 Credits
Built with [yt-dlp](https://github.com/yt-dlp/yt-dlp)
