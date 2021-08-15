define(`GIT_VERSION', ifdef(`GIT_VERSION', GIT_VERSION, 2.5.3))

WGET(https://www.kernel.org/pub/software/scm/git/git-GIT_VERSION.tar.gz)
RUN tar xzf git-GIT_VERSION.tar.gz
RUN cd git-GIT_VERSION && make && make install
RUN rm -rf git-GIT_VERSION git-GIT_VERSION.tar.gz
