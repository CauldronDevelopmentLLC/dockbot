define(`TWISTED_VERSION', ifdef(`TWISTED_VERSION', TWISTED_VERSION, 15.5.0))
define(`TWISTED_BASE', Twisted-TWISTED_VERSION)
define(`TWISTED_PKG', TWISTED_BASE.tar.bz2)
define(`TWISTED_VERSION_DIR', regexp(TWISTED_VERSION, `^[0-9]+\.[0-9]+', `\&'))

WGET(http://twistedmatrix.com/Releases/Twisted/TWISTED_VERSION_DIR/TWISTED_PKG)

RUN tar xf TWISTED_PKG &&\
  (cd Twisted-TWISTED_VERSION; python setup.py install) &&\
  rm -rf TWISTED_PKG TWISTED_BASE
