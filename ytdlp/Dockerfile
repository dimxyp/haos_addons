FROM python:3.11-slim

# Ensure stdout/stderr are unbuffered so print()/traceback output shows up
# immediately in the Home Assistant add-on log viewer instead of being
# buffered and lost.
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y ffmpeg unzip curl && apt-get clean

# Install Deno (JS runtime required by yt-dlp for YouTube extraction)
RUN curl -fsSL https://deno.land/install.sh | sh -s -- -y \
    && mv /root/.deno/bin/deno /usr/local/bin/deno
ENV PATH="/usr/local/bin:${PATH}"

# Install yt-dlp and Flask
RUN pip install --no-cache-dir -U yt-dlp flask

# Create working directory
WORKDIR /app

# Copy app code
COPY app.py .

# Expose Flask port
EXPOSE 5000

# Run Flask app
CMD ["python", "app.py"]
