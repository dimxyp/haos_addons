FROM homeassistant/amd64-base:latest

# Install dependencies
RUN apk add --no-cache python3 py3-pip bash curl jq netcat-openbsd

# Install Azure CLI
RUN apk add --no-cache --virtual=build gcc musl-dev python3-dev libffi-dev openssl-dev cargo make \
    && pip3 install --no-cache-dir --prefer-binary azure-cli flask \
    && apk del build \
    # Fix broken az.completion reference in .bashrc
    && echo '# Clean .bashrc for container\n' > /root/.bashrc

# Copy the script
COPY app.py /app.py

CMD ["python3", "/app.py"]
