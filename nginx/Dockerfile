FROM miracle/base
MAINTAINER CoMSES Net "info@openabm.org"

ARG siteconf="local.conf"

COPY nginx.repo /etc/yum.repos.d/

RUN yum -y update; yum -y install nginx;

COPY nginx.conf /etc/nginx/
COPY $siteconf /etc/nginx/sites-enabled/

COPY dhparam.pem /etc/nginx/ssl/dhparam.pem
COPY server.crt /etc/nginx/ssl/
COPY server.key /etc/nginx/ssl/

ENV TERM xterm

EXPOSE 80 443 

CMD ["nginx", "-g", "daemon off;"]
