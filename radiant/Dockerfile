FROM centos:7

ENV user_id 1000
ENV user_name miracle

RUN yum -y update && yum clean all && yum -y install \
    wget \
    git \
    ed \
    libcurl-devel \
    gcc-c++

RUN useradd -u $user_id $user_name

WORKDIR /opt/
# Install R
RUN wget https://mran.revolutionanalytics.com/install/RRO-3.2.1-el7.x86_64.tar.gz; \
    tar xzf RRO-3.2.1-el7.x86_64.tar.gz; \
    cd RRO-3.2.1 && ./install.sh; \
    cd /opt/ && rm -rf RRO-3.2.1-el7.x86_64.tar.gz && rm -rf RRO-3.2.1
# Install necessary R packages
RUN R -e "install.packages(c('shiny', 'rmarkdown'), repos='https://cran.rstudio.com/')"
# Install Shiny Server
RUN wget https://download3.rstudio.org/centos5.9/x86_64/shiny-server-1.4.0.721-rh5-x86_64.rpm; \
	yum install -y --nogpgcheck shiny-server-1.4.0.721-rh5-x86_64.rpm; \
	rm -rf shiny-server-1.4.0.721-rh5-x86_64.rpm
# Install Radiant
RUN R -e "install.packages('radiant', repos='http://vnijs.github.io/radiant_miniCRAN/')"
RUN git clone --depth 1 https://github.com/warmdev/radiant-mod.git; \
	cp -r radiant-mod/inst/* /srv/shiny-server; cp -r radiant-mod/R /srv; \
	rm -rf radiant-mod;
# Add starting script
RUN sed -i -e 's/run_as shiny/run_as miracle/g' /etc/shiny-server/shiny-server.conf
ADD shiny-server.sh /usr/bin/shiny-server.sh
USER root
RUN chmod +x /usr/bin/shiny-server.sh
RUN chown $user_name:$user_name /usr/bin/shiny-server.sh
RUN mkdir -p /var/log/shiny-server
RUN touch /var/log/shiny-server.log
RUN chown $user_name:$user_name /var/log/shiny-server.log
RUN chown $user_name:$user_name /var/log/shiny-server

USER $user_name
EXPOSE 3838

CMD ["/usr/bin/shiny-server.sh"]
