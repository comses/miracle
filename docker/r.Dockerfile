FROM miracle/base

RUN yum -y update
RUN wget https://mran.revolutionanalytics.com/install/mro/3.2.3/MRO-3.2.3.el7.x86_64.rpm; \
    yum install -y MRO-3.2.3.el7.x86_64.rpm; rm -rf MRO-3.2.3.el7.x86_64.rpm
RUN sed -i "4s/.*/R_HOME_DIR=\/usr\/lib64\/MRO-3.2.3\/R-3.2.3\/lib64\/R/g" /usr/lib64/MRO-3.2.3/R-3.2.3/lib64/R/bin/R
RUN R -e "install.packages(c('shiny', 'rmarkdown', 'data.table','raster','rasterVis', 'sqldf', 'lattice', 'latticeExtra', 'RPostgreSQL'), repos='https://cran.rstudio.com/')"
RUN R -e "install.packages('radiant', repos='http://vnijs.github.io/radiant_miniCRAN/')"
