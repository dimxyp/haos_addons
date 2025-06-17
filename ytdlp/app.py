from flask import Flask, request, jsonify
import subprocess
import os
import uuid

app = Flask(__name__)

@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    url = data.get('url')
    media_type = data.get('type', 'video')  # default to video

    if not url:
        return jsonify({"error": "Missing URL"}), 400

    job_id = str(uuid.uuid4())[:8]
    output_base = f"/tmp/{job_id}"

    if media_type == "audio":
        output_file = f"{output_base}.mp3"
        command = [
            "yt-dlp",
            "-f", "bestaudio",
            "--extract-audio",
            "--audio-format", "mp3",
            "-o", output_file,
            url
        ]
    else:
        output_file = f"{output_base}.mp4"
        command = [
            "yt-dlp",
            "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
            "-o", output_file,
            url
        ]

    try:
        subprocess.run(command, check=True)
        return jsonify({
            "status": "success",
            "file_path": output_file,
            "type": media_type
        }), 200
    except subprocess.CalledProcessError as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5903)
