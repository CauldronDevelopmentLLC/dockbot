define(`ZOPE_VERSION', ifdef(`ZOPE_VERSION', ZOPE_VERSION, 3.3.0))
define(`ZOPE_BASE', zope.interface-ZOPE_VERSION)
define(`ZOPE_PKG', ZOPE_BASE.tar.gz)

WGET(http://www.zope.org/Products/ZopeInterface/ZOPE_VERSION/ZOPE_PKG)

RUN tar xf ZOPE_PKG &&\
  (cd ZOPE_BASE; python setup.py install) &&\
  rm -rf ZOPE_BASE ZOPE_PKG
