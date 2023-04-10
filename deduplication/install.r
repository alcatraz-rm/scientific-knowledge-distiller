# install devtools

install.packages("devtools", repos="http://cran.us.r-project.org")

# remove.packages("ASySD")

# package on github is broken
devtools::install_github("camaradesuk/ASySD")

# install local fixed ASySD
devtools::install_local("ASySD")
