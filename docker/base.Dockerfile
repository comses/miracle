FROM miracle/min

RUN yum -y update; yum -y install epel-release
RUN yum -y install wget psmisc gcc gcc-c++ which nano ed git supervisor p7zip p7zip-plugins redis
RUN yum -y install python-pip python-setuptools python-devel gdal-python
RUN yum -y install libffi-devel libicu-devel libcurl-devel pango-devel postgresql-devel librsvg2-devel
