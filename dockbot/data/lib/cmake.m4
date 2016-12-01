define(`CMAKE_VERSION', ifdef(`CMAKE_VERSION', CMAKE_VERSION, 3.7.0))
define(`CMAKE_ROOT', cmake-CMAKE_VERSION)
define(`CMAKE_PKG', CMAKE_ROOT.tar.gz)
define(`CMAKE_VERSION_DIR', regexp(CMAKE_VERSION, `^[0-9]+\.[0-9]+', `v\&'))

WGET(https://cmake.org/files/CMAKE_VERSION_DIR/CMAKE_PKG)

RUN tar xf CMAKE_PKG &&\
  cd CMAKE_ROOT &&\
  ./configure --prefix=/usr &&\
  make -j CONCURRENCY &&\
  make install
