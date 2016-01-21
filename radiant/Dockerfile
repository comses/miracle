# Radiant and Shiny Dockerfile

# Mount Points
# /var/log/shiny-server.log     log file
# /miracle/projects             project files

FROM centos:7

ENV user_id 1000
ENV user_name miracle
ENV projects_path /miracle/projects

RUN yum -y update && yum clean all && yum -y install \
    wget \
    git \
    ed \
    libcurl-devel \
    gcc-c++ \
    pango-devel

RUN useradd -u $user_id $user_name

WORKDIR /opt/
# Install R
RUN wget https://mran.revolutionanalytics.com/install/RRO-3.2.2.el7.x86_64.rpm \
    && yum install -y RRO-3.2.2.el7.x86_64.rpm; rm -rf RRO-3.2.2.el7.x86_64.rpm

RUN sed -i "4s/.*/R_HOME_DIR=\/usr\/lib64\/RRO-3.2.2\/R-3.2.2\/lib64\/R/g" /usr/lib64/RRO-3.2.2/R-3.2.2/lib64/R/bin/R

# Install necessary R packages
RUN R -e "install.packages(c('shiny', 'rmarkdown'), repos='https://cran.rstudio.com/')"

# Install Shiny Server
RUN wget https://download3.rstudio.org/centos5.9/x86_64/shiny-server-1.4.0.756-rh5-x86_64.rpm; \
	yum install -y --nogpgcheck shiny-server-1.4.0.756-rh5-x86_64.rpm; \
	rm -rf shiny-server-1.4.0.756-rh5-x86_64.rpm

# Install Radiant
RUN R -e "install.packages('radiant', repos='http://vnijs.github.io/radiant_miniCRAN/')"
RUN git clone --depth 1 https://github.com/warmdev/radiant-mod.git radiant \
	&& cp -r radiant /srv/shiny-server \
	&& cd /opt; rm -rf radiant \
    && cp -r /srv/shiny-server/radiant/inst/* /srv/shiny-server \
    && cp -r /srv/shiny-server/radiant/R /srv \
    && rm -rf /srv/shiny-server/radiant

# Hardwired Libraries for luxedemo -- can remove later
RUN R -e "install.packages(c('data.table','raster','rasterVis', 'sqldf', 'lattice', 'latticeExtra'), repos='https://cran.rstudio.com/')"

# Configure Shiny and Radiant
# ---------------------------
RUN sed -i -e 's/run_as shiny/run_as miracle/g' /etc/shiny-server/shiny-server.conf
ADD shiny-server.sh /usr/bin/shiny-server.sh
USER root
RUN mkdir -p $projects_path \
    && ln -s $projects_path /srv/shiny-server/apps \
    && chown -R $user_name:$user_name $projects_path
RUN chmod +x /usr/bin/shiny-server.sh \
    && chown $user_name:$user_name /usr/bin/shiny-server.sh
# Create a log file
RUN mkdir -p /var/log/shiny-server \
    && touch /var/log/shiny-server.log \
    && chown $user_name:$user_name /var/log/shiny-server.log \
    && chown -R $user_name:$user_name /var/log/shiny-server

USER $user_name
EXPOSE 3838

CMD ["/usr/bin/shiny-server.sh"]
