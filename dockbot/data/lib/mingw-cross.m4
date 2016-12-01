# Setup cross compiler
RUN \
  ln -s /usr/bin/MINGW_PREFIX`windres' /usr/bin/windres &&\
  ln -s /usr/bin/MINGW_PREFIX`gcc' /usr/bin/MINGW_PREFIX`cc' &&\
  for i in gcc g++ cc c++ ld strip; do\
    update-alternatives --install /usr/bin/$i $i /usr/bin/MINGW_PREFIX$i 10 &&\
    update-alternatives --set $i /usr/bin/MINGW_PREFIX$i ||\
    exit 1;\
  done

# Fix CMake cross-compile
RUN sed -i 's/^\(.*"-rdynamic".*\)$/#\1/' \
  /usr/share/cmake-*/Modules/Platform/Linux-GNU.cmake

ENV C_INCLUDE_PATH=MINGW_ROOT/include CPLUS_INCLUDE_PATH=MINGW_ROOT/include \
  LD_LIBRARY_PATH=MINGW_ROOT/include PKG_CONFIG_PATH=MINGW_ROOT/lib/pkgconfig
