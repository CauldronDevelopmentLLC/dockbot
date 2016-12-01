# Build missing std::ios_base::failure constructor using clang w/ c++11 support
RUN printf '\
  %cinclude <ios>\n\
  namespace std {\
    ios_base::failure::failure(string const &msg) :\
      system_error(error_code(), msg) {}\
  }' \# > failure.cpp &&\
  MINGW_ROOT/bin/MINGW_ARCH-w64-mingw32-clang++ -c failure.cpp -std=c++11 \
    -Wall -Werror

# Inject the resulting .o into libstdc++.dll.a so it is automatically linked in
RUN mkdir /tmp/libstdc++ &&\
  cd /tmp/libstdc++ &&\
  ar x /usr/lib/gcc/MINGW_ARCH-w64-mingw32/6.1-win32/libstdc++.dll.a &&\
  cp /failure.o . &&\
  ar rcs ../libstdc++.dll.a * &&\
  cd .. &&\
  rm -rf libstdc++ &&\
  mv libstdc++.dll.a /usr/lib/gcc/MINGW_ARCH-w64-mingw32/6.1-win32/
