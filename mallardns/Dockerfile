ARG BUILD_FROM
FROM $BUILD_FROM

# Setup base
ARG DEHYDRATED_VERSION
# Install openssh-client
RUN apk add --no-cache openssh
RUN apk add --no-cache openssl \
  && curl -s -o /usr/bin/dehydrated \
    "https://raw.githubusercontent.com/Xebozone/dehydrated/${DEHYDRATED_VERSION}/dehydrated" \
  && chmod a+x /usr/bin/dehydrated

# Copy root filesystem 
COPY rootfs /
RUN [ -f /root/hooks.sh ] && chmod +x /root/hooks.sh || echo "No hooks.sh found"
