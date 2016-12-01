#define(`NODE_VERSION', ifdef(`NODE_VERSION', NODE_VERSION, ???))
define(`NODE_BASE', `node-v'NODE_VERSION)
define(`NODE_PKG', NODE_BASE.tar.gz)

WGET(http://nodejs.org/dist/`v'NODE_VERSION/NODE_PKG)

RUN tar xf NODE_PKG &&\
  cd NODE_BASE &&\
  ./configure &&\
  make -j CONCURRENCY &&\
  make install &&\
  cd .. &&\
  rm -rf NODE_PKG NODE_BASE
