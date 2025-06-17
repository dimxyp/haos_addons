FROM python:3.11-slim

# Install yt-dlp and dependencies
RUN pip install --no-cache-dir yt-dlp flask

# Create working directory
WORKDIR /app

# Copy app code
COPY app.py .

# Expose Flask port
EXPOSE 5000

# Run Flask app
CMD ["python", "app.py"]
