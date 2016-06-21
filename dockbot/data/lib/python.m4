# download
RUN wget --quiet \
  https://www.python.org/ftp/python/$PYTHON_VERSION/Python-$PYTHON_VERSION.tgz

# unpack
RUN tar xf Python-$PYTHON_VERSION.tgz && rm Python-$PYTHON_VERSION.tgz

# configure, build, install & clean
RUN cd Python-$PYTHON_VERSION && \
  mkdir build && \
  cd build && \
  ../configure --enable-shared --prefix=/usr && \
  make -j$(grep -c ^processor /proc/cpuinfo) && \
  make install && \
  ldconfig && \
  cd ../.. && \
  rm -rf Python-$PYTHON_VERSION
