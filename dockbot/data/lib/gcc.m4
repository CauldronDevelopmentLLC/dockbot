define(`GCC_VERSION', ifdef(`GCC_VERSION', GCC_VERSION, 4.8.5))
define(`GCC_BASE', gcc-GCC_VERSION)
define(`GCC_PKG', GCC_BASE.tar.bz2)
define(`GCC_NJOBS', ifdef(`GCC_NJOBS', GCC_NJOBS, CONCURRENCY))

# download
RUN wget --quiet https://ftp.gnu.org/gnu/gcc/GCC_BASE/GCC_PKG ||\
  wget --quiet http://www.netgull.com/gcc/releases/GCC_BASE/GCC_PKG

# unpack
RUN tar xf GCC_PKG && rm GCC_PKG

# prerequisites
RUN cd GCC_BASE && ./contrib/download_prerequisites > /dev/null

# configure, build & install
RUN cd GCC_BASE &&\
  mkdir build &&\
  cd build &&\
  ../configure --enable-languages=c,c++ --disable-multilib --disable-bootstrap \
    --prefix=/usr &&\
  make -j GCC_NJOBS &&\
  make install &&\
  cd ../.. &&\
  rm -rf GCC_BASE
