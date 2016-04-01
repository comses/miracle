# Radiant and Shiny Dockerfile

# Mount Points
# /var/log/shiny-server.log     log file
# /miracle/projects             project files

FROM miracle/r

ENV projects_path /miracle/projects

WORKDIR /opt/

# Install Shiny Server
RUN wget https://download3.rstudio.org/centos5.9/x86_64/shiny-server-1.4.2.786-rh5-x86_64.rpm; \
	yum install -y --nogpgcheck shiny-server-1.4.2.786-rh5-x86_64.rpm; \
	rm -rf shiny-server-1.4.2.786-rh5-x86_64.rpm

# Install Radiant
RUN git clone --depth 1 https://github.com/warmdev/radiant-mod.git radiant \
	&& cp -r radiant /srv/shiny-server \
	&& cd /opt; rm -rf radiant \
    && cp -r /srv/shiny-server/radiant/inst/* /srv/shiny-server \
    && cp -r /srv/shiny-server/radiant/R /srv \
    && rm -rf /srv/shiny-server/radiant

# Configure Shiny and Radiant
# ---------------------------
RUN sed -i -e 's/run_as shiny/run_as miracle/g' /etc/shiny-server/shiny-server.conf
ADD shiny-server.sh /usr/bin/shiny-server.sh
USER root
RUN mkdir -p $projects_path \
    && ln -s $projects_path /srv/shiny-server/miracle \
    && chown -R miracle:miracle $projects_path
RUN chmod +x /usr/bin/shiny-server.sh \
    && chown miracle:miracle /usr/bin/shiny-server.sh
# Create a log file
RUN mkdir -p /var/log/shiny-server \
    && touch /var/log/shiny-server.log \
    && chown miracle:miracle /var/log/shiny-server.log \
    && chown -R miracle:miracle /var/log/shiny-server

ENV TERM xterm

USER miracle
EXPOSE 3838

CMD ["/usr/bin/shiny-server.sh"]
