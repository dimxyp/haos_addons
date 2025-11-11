FROM homeassistant/amd64-base:latest

# Install Python3, pip, Chrome/Chromedriver, and necessary runtime deps
RUN apk add --no-cache \
    python3 \
    py3-pip \
    bash \
    udev \
    chromium \
    chromium-chromedriver \
    harfbuzz \
    nss \
    ttf-freefont \
    dbus-glib \
    mesa-dri-gallium \
    mesa-gbm \
    libstdc++ \
    ffmpeg && \
    pip3 install --no-cache-dir selenium webdriver-manager requests

ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver
ENV CHROME_BIN=/usr/bin/chromium-browser

# Copy all .py files in the context to your working directory
COPY *.py /opt/selenium/

WORKDIR /opt/selenium