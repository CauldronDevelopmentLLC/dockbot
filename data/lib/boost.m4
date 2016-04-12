RUN echo boost_$BOOST_VERSION | tr . _ > boost_pkg

RUN wget --quiet http://downloads.sourceforge.net/project/boost/boost/$BOOST_VERSION/$(cat boost_pkg).tar.bz2

RUN tar xf $(cat boost_pkg).tar.bz2 \
  $(cat boost_pkg)/libs/regex \
  $(cat boost_pkg)/libs/filesystem \
  $(cat boost_pkg)/libs/system \
  $(cat boost_pkg)/libs/iostreams \
  $(cat boost_pkg)/boost

RUN rm $(cat boost_pkg).tar.bz2 boost_pkg
