# Snappy
RUN wget --quiet \
  https://github.com/google/snappy/releases/download/1.1.3/snappy-1.1.3.tar.gz
RUN tar xf snappy-1.1.3.tar.gz && rm snappy-1.1.3.tar.gz
RUN cd snappy-1.1.3 && \
  CXXFLAGS=-fPIC ./configure --enable-shared=no && \
  make && \
  make install

# LevelDB
RUN wget --quiet https://github.com/google/leveldb/archive/v1.18.tar.gz
RUN tar xf v1.18.tar.gz && rm v1.18.tar.gz
RUN cd leveldb-1.18 && \
  make && \
  cp libleveldb.a /usr/lib && \
  cp -av include/leveldb/ /usr/include/
