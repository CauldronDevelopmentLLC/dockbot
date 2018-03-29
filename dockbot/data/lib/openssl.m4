define(`OPENSSL_VERSION', ifdef(`OPENSSL_VERSION', OPENSSL_VERSION, 1.1.0c))
define(`OPENSSL_CONFIG', ifdef(`OPENSSL_CONFIG', OPENSSL_CONFIG, ))
define(`OPENSSL_BASE', openssl-OPENSSL_VERSION)
define(`OPENSSL_PKG', OPENSSL_BASE.tar.gz)

WGET(http://www.openssl.org/source/OPENSSL_PKG)

RUN tar xf OPENSSL_PKG &&\
  cd OPENSSL_BASE &&\
  ./config --prefix=/usr OPENSSL_CONFIG &&\
  make &&\
  make install &&\
  cd .. &&\
  rm -rf OPENSSL_BASE OPENSSL_PKG
