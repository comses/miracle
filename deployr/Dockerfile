# DeployR Dockerfile

# Mount Points
# /home/deployr/deployr/8.0.0/deployr/database  MongoDB 

FROM miracle/r

USER root
WORKDIR /opt/
ENV JDK_RPM jdk-8u91-linux-x64.rpm
ENV JDK_URL 8u91-b14/$JDK_RPM
RUN wget --no-cookies --no-check-certificate --header \
        "Cookie: gpw_e24=http%3A%2F%2Fwww.oracle.com%2F; oraclelicense=accept-securebackup-cookie" \
        "http://download.oracle.com/otn-pub/java/jdk/$JDK_URL"; \
    yum install -y $JDK_RPM
RUN wget https://github.com/deployr/deployr-rserve/releases/download/v7.4.2/deployrRserve_7.4.2.tar.gz; \
    R CMD INSTALL deployrRserve_7.4.2.tar.gz; \
    rm -rf deployrRserve_7.4.2.tar.gz

USER miracle
WORKDIR /home/miracle/
RUN mkdir download; \
    wget http://deployr.revolutionanalytics.com/download/bundles/release/DeployR-Open-Linux-8.0.0.tar.gz -P download; \
    cd download && tar xzf DeployR-Open-Linux-8.0.0.tar.gz
COPY installDeployROpen.sh download/installFiles/

USER root
RUN chown miracle:miracle download/installFiles/installDeployROpen.sh && \
    mkdir -p /miracle/projects && \
    chown -R miracle:miracle /miracle

USER miracle
RUN cd download/installFiles/ && export JAVA_HOME=/usr/java/latest && chmod +x installDeployROpen.sh && sync && ./installDeployROpen.sh --no-ask --nolicense
COPY startAll.sh deployr/8.0.0/

USER root
# Hardwired Libraries for luxedemo -- can remove later
RUN pip install pymongo uuid bcrypt
RUN chown miracle:miracle deployr/8.0.0/startAll.sh
RUN chmod +x deployr/8.0.0/startAll.sh && sync && ln -s /miracle/projects /home/miracle/deployr/8.0.0/deployr/external/data/public
RUN rm -rf download

COPY addUser.py /home/miracle/
RUN chown miracle: /home/miracle/addUser.py && chmod a+x /home/miracle/addUser.py

ENV TERM xterm
EXPOSE 8000 8006

USER miracle
CMD ["/home/miracle/deployr/8.0.0/startAll.sh"]
