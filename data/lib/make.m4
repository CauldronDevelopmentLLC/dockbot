RUN wget --quiet http://ftp.gnu.org/gnu/make/make-4.1.tar.bz2
RUN tar xf make-4.1.tar.bz2 && rm make-4.1.tar.bz2
RUN cd make-4.1 && \
  ./configure --prefix=/usr && \
  make && \
  make install
