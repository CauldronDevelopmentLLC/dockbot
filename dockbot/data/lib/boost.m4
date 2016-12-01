define(`BOOST_VERSION', ifdef(`BOOST_VERSION', BOOST_VERSION, 1.62.0))
define(`BOOST_BASE', `boost_'translit(BOOST_VERSION, `.', `_'))
define(`BOOST_PKG', BOOST_BASE.tar.bz2)

ENV BOOST_SOURCE=$HOME/BOOST_BASE `BOOST_VERSION'=BOOST_VERSION

WGET(
  http://downloads.sourceforge.net/project/boost/boost/BOOST_VERSION/BOOST_PKG)

RUN tar xf BOOST_PKG BOOST_BASE/libs/regex BOOST_BASE/libs/filesystem \
  BOOST_BASE/libs/system BOOST_BASE/libs/iostreams BOOST_BASE/boost &&\
  rm BOOST_PKG
