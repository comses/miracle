FROM miracle/base

ENV PYTHONUNBUFFERED 1

ARG reqfile="local.txt"

COPY requirements/base.txt requirements/$reqfile /tmp/
RUN pip install -r /tmp/$reqfile

RUN echo "INSTALLING requirements from $reqfile"

# set up shared volumes permissions - we create them and chown them because mounted volumes inherit the ownership
# and permissions set prior

RUN for d in projects packrat static archives socket logs; do mkdir -p /miracle/$d; done; chown -R miracle: /miracle;

ENV TERM xterm

USER miracle
WORKDIR /code/django
CMD ["/code/django/entrypoint.sh"]
