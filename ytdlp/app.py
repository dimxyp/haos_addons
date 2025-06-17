from flask import Flask, request, jsonify
import subprocess
import os

app = Flask(__name__)

MEDIA_PATH = "/media"

@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    url = data.get('url')
    media_type = data.get('type')  # "video" or "audio"

    if not url or media_type not in ("video", "audio"):
        return jsonify({"error": "Missing or invalid parameters"}), 400

    subfolder = request.args.get("subfolder", "ytdowns")
    target_dir = os.path.join(MEDIA_PATH, subfolder, media_type)
    os.makedirs(target_dir, exist_ok=True)

    if media_type == "video":
        options = ['-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4', '-o', f'{target_dir}/%(title)s.%(ext)s']
    else:  # audio
        options = ['-x', '--audio-format', 'mp3', '-o', f'{target_dir}/%(title)s.%(ext)s']

    try:
        subprocess.run(['yt-dlp', url] + options, check=True)
        return jsonify({"status": "success", "saved_to": target_dir})
    except subprocess.CalledProcessError as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def index():
    return "yt-dlp downloader is running."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5903)
