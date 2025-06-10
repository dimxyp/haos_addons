FROM homeassistant/amd64-base:latest

# Install dependencies
RUN apk add --no-cache python3 py3-pip bash curl jq
EXPOSE 5902
# Install Azure CLI
RUN apk add --no-cache --virtual=build gcc musl-dev python3-dev libffi-dev openssl-dev cargo make \
    && pip3 install --no-cache-dir --prefer-binary azure-cli \
    && apk del build

# Copy and set up the script
COPY run.sh /run.sh
RUN chmod +x /run.sh

CMD ["/run.sh"]
