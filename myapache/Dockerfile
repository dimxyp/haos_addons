ARG BUILD_FROM
# hadolint ignore=DL3006
FROM ${BUILD_FROM}

# Create directory for apache2 to store PID file
RUN mkdir /run/apache2

RUN apk --no-cache add apache2 php7.0-apache2 libxml2-dev apache2-utils apache2-mod-wsgi apache2-ssl apache2-proxy
RUN apk --no-cache add php7.0 php7.0-dev php7.0-fpm php7.0-mysqli php7.0-opcache php7.0-gd zlib php7.0-curl php7.0-phar \
php7.0-mbstring php7.0-zip php7.0-pdo php7.0-pdo_mysql php7.0-iconv php7.0-dom php7.0-session php7.0-intl php7.0-soap php7.0-fileinfo \
php7.0-xml php7.0-ctype php7.0-pecl-xdebug php7.0-pdo_sqlite php7.0-tokenizer php7.0-exif php7.0-xmlwriter php7.0-cgi php7.0-simplexml \
php7.0-sockets
RUN apk --no-cache add \
    php7.0-simplexml \
    php7.0-gd \
    php7.0-json \
    php7.0-imap \
    php7.0-apcu \
    php7.0-fpm \
    php7.0-opcache \
    php7.0-session \
    php7.0-json \
    php7.0-mbstring \
    php7.0-gettext \
    php7.0-pdo \
    php7.0-pdo_sqlite \
    php7.0-sqlite3 \
    php7.0-curl \
    php7.0-xml \
    php7.0-openssl

RUN apk --no-cache add mosquitto mosquitto-dev
RUN apk --no-cache add mariadb-client
RUN apk --no-cache add ffmpeg

#musl-locales/php-locales
RUN apk add --no-cache cmake make musl-dev gcc gettext-dev libintl
RUN wget https://gitlab.com/rilian-la-te/musl-locales/-/archive/master/musl-locales-master.zip \
    && unzip musl-locales-master.zip \
    && cd musl-locales-master \
    && cmake -DLOCALE_PROFILE=OFF -D CMAKE_INSTALL_PREFIX:PATH=/usr . && make && make install \
    && cd .. && rm -r musl-locales-master

# Install ssh2 extension
#RUN apk --no-cache add libssh2-dev php7.0-pear zlib-dev build-base
#RUN pecl channel-update pecl.php.net \
#    && pecl install ssh2-1.3.1
#RUN docker-php-ext-enable ssh2
#From here beginning most likely needed
#RUN apk --no-cache add libssh2-dev
#RUN wget -O ssh2.tgz https://pecl.php.net/get/ssh2-1.3.1.tgz \
#    && mkdir ssh2 && tar vxzf ssh2.tgz -C ssh2 --strip-components 1 \
#    && cd ../ssh2 && phpize81 \
#    && ./configure --with-ssh2 --with-php-config=/etc/php7.0/php.ini \
#    && make && make install \
#    && cd ../ && rm -rf ssh2.tgz ssh2

#Configure Logging
RUN sed -i -r 's@Errorlog .*@Errorlog /dev/stderr@i' /etc/apache2/httpd.conf
RUN echo "Transferlog /dev/stdout" >> /etc/apache2/httpd.conf

# Copy data for add-on
COPY run.sh /
COPY index.html /
RUN chmod a+x /run.sh
RUN chmod a+x /index.html
CMD [ "/run.sh" ]
