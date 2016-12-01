define(`PYTHON_VERSION', ifdef(`PYTHON_VERSION', PYTHON_VERSION, 1.62.0))
define(`PYTHON_BASE', Python-PYTHON_VERSION)
define(`PYTHON_PKG', PYTHON_BASE.tgz)

WGET(https://www.python.org/ftp/python/PYTHON_VERSION/PYTHON_PKG)

RUN tar xf PYTHON_PKG &&\
  cd PYTHON_BASE &&\
  mkdir build &&\
  cd build &&\
  ../configure --enable-shared --prefix=/usr &&\
  make -j CONCURRENCY &&\
  make install &&\
  ldconfig &&\
  cd ../.. &&\
  rm -rf PYTHON_PKG PYTHON_BASE
