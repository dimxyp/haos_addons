FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

# Install yt-dlp and Flask
RUN pip install --no-cache-dir yt-dlp flask

# Create working directory
WORKDIR /app

# Copy app code
COPY app.py .

# Expose Flask port
EXPOSE 5000

# Run Flask app
CMD ["python", "app.py"]
