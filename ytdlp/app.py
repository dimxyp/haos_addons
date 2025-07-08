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

@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    url = data.get('download_url')
    media_type = data.get('media_type')

    if not url or media_type not in ("video", "audio", "stream"):
        return jsonify({"error": "Missing or invalid parameters"}), 400

    if media_type == "stream":
        try:
            result = subprocess.run(
                ['yt-dlp', '-f', 'bestaudio', '--get-url', url],
                capture_output=True,
                text=True,
                check=True
            )
            stream_url = result.stdout.strip()
            return jsonify({"status": "success", "stream_url": stream_url})
        except subprocess.CalledProcessError as e:
            return jsonify({"error": "yt-dlp failed", "details": e.stderr}), 500

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
            '--prefer-ffmpeg',
            '--ffmpeg-location', '/usr/bin/ffmpeg',
            '-o', f'{target_dir}/%(title)s.%(ext)s'
        ]

    try:
        subprocess.run(['yt-dlp', url] + options, check=True)
        return jsonify({"status": "success", "saved_to": target_dir})
    except subprocess.CalledProcessError as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def index():
    return "yt-dlp unified streamer/downloader is running."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5903)
