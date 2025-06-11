FROM php:7.0-apache

# Install dependencies for SQLite and other PHP extensions
RUN apt-get update && apt-get install -y \
    libsqlite3-dev \
    libzip-dev \
    unzip \
    && docker-php-ext-install pdo pdo_sqlite sqlite3 \
    && a2enmod rewrite headers

# Copy your app files to Apache web root (adjust as needed)
# COPY ./ipam /var/www/html/ipam

# Set working directory (optional)
WORKDIR /var/www/html

# Expose port 80 (default Apache port)
EXPOSE 80