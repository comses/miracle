FROM comses/miracle-base

ENV PYTHONUNBUFFERED 1

ARG reqfile="local.txt"

RUN yum install -y epel-release && yum install -y python-pip python-setuptools python-devel gdal-python p7zip \
        p7zip-plugins supervisor postgresql-devel libcurl-devel git librsvg2-devel zlib-devel libicu-devel \
        libffi-devel libcurl-devel gcc cronie which \
# set up shared volumes permissions - we create them and chown them because mounted volumes inherit the ownership
# and permissions set prior
        && for d in projects packrat static archives socket logs/supervisor; do mkdir -p /miracle/$d; done \
            && chown -R $USERNAME: /miracle;


COPY requirements/base.txt requirements/$reqfile /tmp/
RUN pip install -q -r /tmp/$reqfile

WORKDIR /code/django
CMD ["/code/deploy/docker/dev.sh"]
