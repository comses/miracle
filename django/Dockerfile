FROM miracle/base

ENV PYTHONUNBUFFERED 1

COPY requirements/base.txt requirements/production.txt /tmp/
RUN pip install -r /tmp/production.txt
RUN mkdir -p /code/logs/supervisor
WORKDIR /code
COPY . /code/

# Create data directories and set permissions
RUN mkdir -p /miracle/packrat /miracle/archives /miracle/projects /miracle/socket /miracle/static; \
     chown -R miracle: /miracle

# Set code directory permission and ownership
RUN chown -R miracle: /code /var/log/supervisor/
RUN chmod +x /code/entrypoint.sh

ENV TERM xterm

USER miracle
CMD ["./entrypoint.sh"]
