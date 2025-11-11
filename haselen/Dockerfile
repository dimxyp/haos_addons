FROM homeassistant/amd64-base:latest

# Install Python3, pip, Chrome, and necessary dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    bash \
    udev \
    chromium \
    chromium-chromedriver \
    # Dependencies for Chrome headless
    harfbuzz \
    nss \
    ttf-freefont \
    dbus-glib \
    mesa-dri-gallium \
    mesa-egl \
    mesa-libegl \
    mesa-gbm \
    mesa-gl \
    mesa-libgl \
    libstdc++ \
    ffmpeg \
    && pip3 install --no-cache-dir \
        selenium \
        webdriver-manager \
        requests

# Optional: Set environment variable so Selenium finds chromedriver
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver
ENV CHROME_BIN=/usr/bin/chromium-browser

# Copy your script into the container (adjust filename as needed)
COPY check_zenith_bill.py /opt/selenium/check_zenith_bill.py

WORKDIR /opt/selenium