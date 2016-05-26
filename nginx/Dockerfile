FROM miracle/base
MAINTAINER CoMSES Net "info@openabm.org"

COPY nginx.repo /etc/yum.repos.d/

RUN yum -y update; yum -y install nginx;

COPY nginx.conf /etc/nginx/
COPY miracle.conf /etc/nginx/sites-enabled/
COPY dhparam.pem /etc/nginx/ssl/dhparam.pem
COPY server.crt /etc/nginx/ssl/
COPY server.key /etc/nginx/ssl/
RUN chown miracle: /etc/nginx/sites-enabled/miracle.conf

VOLUME ["/var/cache/nginx"]

ENV TERM xterm
# forward request and error logs to docker log collector
RUN ln -sf /dev/stdout /var/log/nginx/access.log \
	&& ln -sf /dev/stderr /var/log/nginx/error.log

EXPOSE 80 443 

CMD ["nginx", "-g", "daemon off;"]
