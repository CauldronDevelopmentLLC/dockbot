define(`MAKE_VERSION', ifdef(`MAKE_VERSION', MAKE_VERSION, 4.1))
define(`MAKE_BASE', make-MAKE_VERSION)
define(`MAKE_PKG', MAKE_BASE.tar.bz2)

WGET(http://ftp.gnu.org/gnu/make/MAKE_PKG)

RUN tar xf MAKE_PKG &&\
  cd MAKE_BASE &&\
  ./configure --prefix=/usr &&\
  make -j CONCURRENCY &&\
  make install &&\
  cd .. &&\
  rm -rf MAKE_PKG MAKE_BASE
