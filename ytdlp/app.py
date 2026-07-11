from flask import Flask, request, jsonify
import subprocess
import os
import traceback

#versions on HA
import importlib.metadata
import yt_dlp

flask_version = importlib.metadata.version("flask")
ytdlp_version = yt_dlp.version.__version__

print(f"Starting app with Flask version: {flask_version}")
print(f"Starting app with yt-dlp version: {ytdlp_version}")
# 
app = Flask(__name__)

MEDIA_PATH = "/media"

# Common yt-dlp options: use Deno as JS runtime plus the GitHub-hosted
# remote components (EJS challenge solver script) so YouTube extraction
# works correctly and the client isn't forced to fall back to restricted
# player clients (e.g. android_vr) which can report "This video is not
# available". See: https://github.com/yt-dlp/yt-dlp/wiki/EJS
#
# NOTE: when using the yt-dlp Python API, `js_runtimes` must be a dict of
# {runtime: {config}}, not a list (unlike the CLI --js-runtimes flag).
#
# `noplaylist: True` ensures that when a URL points to a video that is
# also part of a playlist/channel (e.g. a "watch?v=...&list=..." URL),
# yt-dlp extracts just that single video instead of the whole
# playlist/channel (which returns a "_type: playlist" info dict with
# "entries" and no direct "url", causing "No stream URL found").
COMMON_YDL_OPTS = {
    'js_runtimes': {'deno': {}},
    'remote_components': ['ejs:github'],
    'quiet': True,
    'no_warnings': True,
    'noplaylist': True,
}

@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    url = data.get('download_url')
    media_type = data.get('media_type')

    if not url or media_type not in ("video", "audio", "stream"):
        return jsonify({"error": "Missing or invalid parameters"}), 400

    if media_type == "stream":
        # Extract the direct media URL together with the HTTP headers
        # (User-Agent, Cookie, Referer, etc.) that the streaming URL
        # requires. googlevideo.com URLs return 403 Forbidden if these
        # headers are not sent along with the request, which is why
        # opening the plain stream_url in a browser/media player fails
        # even though this endpoint returns 200.
        ydl_opts = dict(COMMON_YDL_OPTS)
        ydl_opts['format'] = 'bestaudio/best'
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                # If we still got a playlist/channel result (e.g. the URL
                # itself is a playlist/channel URL, not just a video that
                # happens to belong to one), fall back to the first entry.
                if info.get('_type') == 'playlist' or 'entries' in info:
                    entries = list(info.get('entries') or [])
                    if not entries:
                        print("ERROR: yt-dlp returned an empty playlist/channel for url=%s" % url)
                        return jsonify({"error": "No video found at URL (empty playlist/channel)"}), 500
                    info = entries[0]

                if 'url' not in info and info.get('requested_formats'):
                    info = info['requested_formats'][0]
                stream_url = info.get('url')
                http_headers = info.get('http_headers', {})
                if not stream_url:
                    print("ERROR: yt-dlp returned no stream URL. Info keys: %s" % list(info.keys()))
                    return jsonify({"error": "No stream URL found"}), 500
                return jsonify({
                    "status": "success",
                    "stream_url": stream_url,
                    "http_headers": http_headers
                })
        except Exception as e:
            print("ERROR in /download (stream): %s" % repr(e))
            traceback.print_exc()
            return jsonify({"error": "yt-dlp failed", "details": str(e)}), 500

    subfolder = request.args.get("subfolder", "ytdowns")
    target_dir = os.path.join(MEDIA_PATH, subfolder, media_type)
    os.makedirs(target_dir, exist_ok=True)

    if media_type == "video":
        options = ['-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4', '-o', f'{target_dir}/%(title)s.%(ext)s']
    else:
        options = [
            '-x',
            '--audio-format', 'mp3',
            '--audio-quality', '0',
            '--ffmpeg-location', '/usr/bin/ffmpeg',
            '-o', f'{target_dir}/%(title)s.%(ext)s'
        ]

    common_opts = ['--js-runtimes', 'deno', '--remote-components', 'ejs:github', '--no-playlist']

    try:
        result = subprocess.run(
            ['yt-dlp'] + common_opts + [url] + options,
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        return jsonify({"status": "success", "saved_to": target_dir})
    except subprocess.CalledProcessError as e:
        print("ERROR in /download (%s): stdout=%s stderr=%s" % (media_type, e.stdout, e.stderr))
        return jsonify({"error": str(e), "stdout": e.stdout, "stderr": e.stderr}), 500

@app.route('/')
def index():
    return "yt-dlp unified streamer/downloader is running."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5903)
