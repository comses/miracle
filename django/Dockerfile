FROM ubuntu:14.04

ENV user_id 1000
ENV user_name miracle

RUN groupadd -r -g $user_id $user_name \
  && useradd -u $user_id -r -s /bin/false -g $user_name $user_name

RUN apt-get update
RUN apt-get install -y \
 python-setuptools \
 python-dev \
 python-pip \
 libpq-dev
RUN pip install --upgrade virtualenv
ENV PYTHONUNBUFFERED 1
RUN apt-get install -y python-gdal p7zip-full redis-server
RUN mkdir /code
WORKDIR /code

ADD . /code/
RUN pip install -r requirements/production.txt

# Create data directories and set permissions
RUN mkdir -p /miracle/packrat /miracle/archives /miracle/projects /miracle/socket \
    && chown -R $user_name:$user_name /miracle

# Set code directory permission
RUN chown -R $user_name:$user_name /code

VOLUME /miracle/projects

USER $user_name
