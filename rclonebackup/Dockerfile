FROM alpine:latest

RUN apk add --no-cache rclone fuse3 bash jq tzdata ca-certificates \
    && echo "user_allow_other" >> /etc/fuse.conf

COPY run.sh /run.sh
RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
