FROM miracle/base

ENV PYTHONUNBUFFERED 1

RUN mkdir /code
WORKDIR /code

ADD . /code/

RUN pip install -r requirements/production.txt

# Create data directories and set permissions
RUN mkdir -p /miracle/packrat /miracle/archives /miracle/projects /miracle/socket /miracle/static; \
     chown -R miracle:miracle /miracle

# Set code directory permission
RUN chown -R miracle:miracle /code
RUN chmod +x /code/entrypoint.sh

ADD supervisord.conf /etc/supervisor/conf.d/

ENV TERM xterm

USER miracle

CMD ["./entrypoint.sh"]
