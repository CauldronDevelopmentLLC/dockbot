# Build clang cross compiler wrapper
RUN git clone --depth=1 https://github.com/cauldrondevelopmentllc/wclang.git
RUN mkdir wclang/build && \
  cd wclang/build && \
  cmake -DCMAKE_INSTALL_PREFIX=MINGW_ROOT .. && \
  make -j CONCURRENCY && \
  make install && \
  cd ../.. && \
  rm -rf wclang
