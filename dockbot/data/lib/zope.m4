RUN wget --quiet \
  http://www.zope.org/Products/ZopeInterface/$ZOPE_VERSION/zope.interface-$ZOPE_VERSION.tar.gz
RUN tar xf zope.interface-$ZOPE_VERSION.tar.gz && \
  rm zope.interface-$ZOPE_VERSION.tar.gz
RUN cd zope.interface-$ZOPE_VERSION; python setup.py install
RUN rm -rf zope.interface-$ZOPE_VERSION
