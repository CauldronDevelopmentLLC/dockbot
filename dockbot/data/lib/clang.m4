RUN svn co http://llvm.org/svn/llvm-project/llvm/trunk llvm &&\
  cd llvm/tools &&\
  svn co http://llvm.org/svn/llvm-project/cfe/trunk clang

# Note that make fails below with -j #
RUN cd llvm &&\
  mkdir build &&\
  cd build &&\
  cmake -G "Unix Makefiles" -DCMAKE_INSTALL_PREFIX=/usr .. &&\
  make &&\
  make install &&\
  cd .. &&\
  rm -rf llvm
