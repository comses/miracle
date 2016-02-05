FROM miracle/base

RUN yum -y update; yum -y install R-core R-core-devel
RUN R -e "install.packages(c('shiny', 'rmarkdown', 'data.table','raster','rasterVis', 'sqldf', 'lattice', 'latticeExtra', 'RPostgreSQL'), repos='https://cran.rstudio.com/')"
RUN R -e "install.packages('radiant', repos='http://vnijs.github.io/radiant_miniCRAN/')"
