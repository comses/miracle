FROM miracle/base

ADD nginx.repo /etc/yum.repos.d/

RUN yum -y update; yum -y install nginx; openssl dhparam -out /etc/ssl/dhparams.pem 4096;

ADD nginx.conf /etc/nginx/
ADD miracle.conf /etc/nginx/sites-enabled/
RUN chown miracle: /etc/nginx/sites-enabled/miracle.conf

VOLUME ["/var/cache/nginx"]

ENV TERM xterm

EXPOSE 80 443 9999

CMD ["nginx", "-g", "daemon off;"]
