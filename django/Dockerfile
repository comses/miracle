FROM miracle/base

ENV PYTHONUNBUFFERED 1

COPY requirements/base.txt requirements/production.txt /tmp/
RUN pip install -r /tmp/production.txt
RUN mkdir -p /code/logs
WORKDIR /code
COPY . /code/

# Create data directories and set permissions
RUN mkdir -p /miracle/packrat /miracle/archives /miracle/projects /miracle/socket /miracle/static; \
     chown -R miracle: /miracle

# Set code directory permission
RUN chown -R miracle: /code
RUN chmod +x /code/entrypoint.sh

RUN ln -sf /dev/stdout /var/log/supervisor/supervisord.log

COPY deploy/supervisord/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

ENV TERM xterm

USER miracle

CMD ["./entrypoint.sh"]
