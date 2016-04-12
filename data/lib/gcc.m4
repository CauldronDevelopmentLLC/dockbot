# download
RUN wget --quiet \
  https://ftp.gnu.org/gnu/gcc/gcc-$GCC_VERSION/gcc-$GCC_VERSION.tar.bz2

# unpack
RUN tar xf gcc-$GCC_VERSION.tar.bz2 && rm gcc-$GCC_VERSION.tar.bz2

# prerequisites
RUN cd gcc-$GCC_VERSION && \
  ./contrib/download_prerequisites > /dev/null

# configure, build & install
RUN cd gcc-$GCC_VERSION && \
  mkdir build && \
  cd build && \
  ../configure --enable-languages=c,c++ --disable-multilib --disable-bootstrap \
    --prefix=/usr && \
  make -j ${GCC_NJOBS-$(grep -c ^processor /proc/cpuinfo)} && \
  make install

# clean up
RUN rm -rf gcc-$GCC_VERSION
