RUN wget --quiet  http://www.openssl.org/source/openssl-$OPENSSL_VERSION.tar.gz
RUN tar xf openssl-$OPENSSL_VERSION.tar.gz && rm openssl-$OPENSSL_VERSION.tar.gz
RUN cd openssl-$OPENSSL_VERSION && \
  ./config --prefix=/usr && \
  make && \
  make install
RUN rm -rf openssl-$OPENSSL_VERSION
