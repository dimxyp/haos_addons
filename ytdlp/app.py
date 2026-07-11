from flask import Flask, request, jsonify
import subprocess
import os

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
COMMON_YDL_OPTS = {
    'js_runtimes': {'deno': {}},
    'remote_components': ['ejs:github'],
    'quiet': True,
    'no_warnings': True,
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
                if 'url' not in info and info.get('requested_formats'):
                    info = info['requested_formats'][0]
                stream_url = info.get('url')
                http_headers = info.get('http_headers', {})
                if not stream_url:
                    return jsonify({"error": "No stream URL found"}), 500
                return jsonify({
                    "status": "success",
                    "stream_url": stream_url,
                    "http_headers": http_headers
                })
        except yt_dlp.utils.DownloadError as e:
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

    common_opts = ['--js-runtimes', 'deno', '--remote-components', 'ejs:github']

    try:
        subprocess.run(['yt-dlp'] + common_opts + [url] + options, check=True)
        return jsonify({"status": "success", "saved_to": target_dir})
    except subprocess.CalledProcessError as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def index():
    return "yt-dlp unified streamer/downloader is running."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5903)
