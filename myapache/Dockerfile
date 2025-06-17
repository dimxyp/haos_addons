FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y ffmpeg \
  && pip install flask yt-dlp

# Copy only app.py
COPY app.py .

EXPOSE 5903

CMD ["python", "app.py"]