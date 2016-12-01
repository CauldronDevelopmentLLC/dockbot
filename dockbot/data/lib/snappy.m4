define(`SNAPPY_VERSION', ifdef(`SNAPPY_VERSION', SNAPPY_VERSION, 1.1.3))
define(`SNAPPY_BASE', snappy-SNAPPY_VERSION)
define(`SNAPPY_PKG', SNAPPY_BASE.tar.gz)

WGET(
https://github.com/google/snappy/releases/download/SNAPPY_VERSION/SNAPPY_PKG)

RUN tar xf SNAPPY_PKG &&\
  cd SNAPPY_BASE &&\
  CXXFLAGS=-fPIC ./configure --enable-shared=no &&\
  make -j CONCURRENCY &&\
  make install &&\
  cd .. &&\
  rm -rf SNAPPY_PKG SNAPPY_BASE
