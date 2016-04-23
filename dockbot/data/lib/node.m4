RUN wget --quiet \
  http://nodejs.org/dist/v$NODE_VERSION/node-v$NODE_VERSION.tar.gz
RUN tar zxf node-v$NODE_VERSION.tar.gz && rm node-v$NODE_VERSION.tar.gz
RUN cd node-v$NODE_VERSION && \
  ./configure && \
  make -j ${GCC_NJOBS-$(grep -c ^processor /proc/cpuinfo)} && \
  make install
RUN rm -rf node-v$NODE_VERSION
