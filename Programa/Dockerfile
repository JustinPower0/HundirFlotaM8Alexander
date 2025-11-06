FROM php:8.2-apache

# Instalar extensiones necesarias
RUN docker-php-ext-install pdo pdo_mysql

# Copiar los archivos del sitio web
COPY ./Programa /var/www/html/

# Dar permisos a Apache
RUN chmod -R 755 /var/www/html

# Apache ya se inicia automáticamente
