FROM homeassistant/amd64-base:latest

# Install Python3, pip, Chromium/Chromedriver, and required dependencies
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
    ffmpeg \
 && pip3 install --no-cache-dir selenium requests

ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver
ENV CHROME_BIN=/usr/bin/chromium-browser

WORKDIR /opt/selenium

# Copy all Python scripts; add more as needed in this folder
COPY *.py /opt/selenium/

# Run the main script in unbuffered mode for correct logging
CMD ["python3", "-u", "/opt/selenium/check_zenith_bill.py"]