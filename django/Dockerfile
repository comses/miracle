FROM ubuntu:14.04

ENV user_id 1000
ENV user_name miracle

RUN groupadd -r $user_name \
  && useradd -u $user_id -r -s /bin/false -g $user_name $user_name

RUN apt-get update
RUN apt-get install -y \
 python-setuptools \
 python-dev \
 python-pip \
 libpq-dev
RUN pip install --upgrade virtualenv
ENV PYTHONUNBUFFERED 1
RUN apt-get install -y python-gdal p7zip-full
RUN mkdir /code
WORKDIR /code
ADD requirements.txt /code/
RUN pip install -r requirements.txt
USER $user_name
ADD . /code/
