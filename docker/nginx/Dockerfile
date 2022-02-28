FROM nginx

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    openssl\
    && rm -rf /var/lib/apt/lists/*\
    && openssl req -x509 -nodes -days 365 -subj "/C=CA/ST=QC/O=Company, Inc./CN=mydomain.com" \
    -addext "subjectAltName=DNS:mydomain.com" -newkey rsa:2048 -keyout /etc/ssl/private/nginx-selfsigned.key \
    -out /etc/ssl/certs/nginx-selfsigned.crt && \
    rm -f /etc/nginx/conf.d/default.conf

RUN mkdir -p /etc/nginx/ssl/certs/ &&\
    mkdir -p /etc/nginx/ssl/certs/ &&\
    cp /etc/ssl/certs/nginx-selfsigned.crt /etc/nginx/ssl/certs/cert.crt && \
    cp /etc/ssl/private/nginx-selfsigned.key /etc/nginx/ssl/certs/key.key 

COPY nginx.conf /etc/nginx/conf.d
COPY docker-entrypoint.sh /

ENTRYPOINT ["./docker-entrypoint.sh"]

EXPOSE 80 443

STOPSIGNAL SIGTERM

CMD ["nginx", "-g", "daemon off;"]