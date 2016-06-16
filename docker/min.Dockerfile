FROM centos:7

ARG MIRACLE_UID=2000

RUN useradd -U -m -u $MIRACLE_UID -s /sbin/nologin miracle
