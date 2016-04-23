RUN wget --quiet \
  http://twistedmatrix.com/Releases/Twisted/${TWISTED_VERSION%.[0-9]*}/Twisted-$TWISTED_VERSION.tar.bz2
RUN tar xf Twisted-$TWISTED_VERSION.tar.bz2 && \
  rm Twisted-$TWISTED_VERSION.tar.bz2
RUN cd Twisted-$TWISTED_VERSION; python setup.py install
RUN rm -rf Twisted-$TWISTED_VERSION
