define(`OSSLSIGNCODE_VERSION', 1.7.1)
define(`OSSLSIGNCODE_ROOT', osslsigncode-OSSLSIGNCODE_VERSION)
define(`OSSLSIGNCODE_PKG', OSSLSIGNCODE_ROOT.tar.gz)
define(`OSSLSIGNCODE_URL_BASE',
  http://downloads.sourceforge.net/project/osslsigncode/osslsigncode)

APT(automake)
WGET(OSSLSIGNCODE_URL_BASE/OSSLSIGNCODE_PKG)

RUN tar xf OSSLSIGNCODE_PKG &&\
  cd OSSLSIGNCODE_ROOT &&\
  ./configure --prefix=/usr &&\
  make -j CONCURRENCY &&\
  make install &&\
  cd .. &&\
  rm -rf OSSLSIGNCODE_ROOT
