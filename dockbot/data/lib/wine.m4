# Setup wine environment
ifelse(ARCH_BITS, 32, RUN dpkg --add-architecture i386)
APT(`wine'ARCH_BITS wine-binfmt)
ifelse(ARCH_BITS, 64,
  RUN sed -i 's/bin\/wine/bin\/wine64/' /usr/share/binfmts/wine)
RUN echo "\nupdate-binfmts --enable wine" >> $HOME/.bashrc

ENV WINEDEBUG=err-all,warn-all,fixme-all,trace-all
ENV WINESERVER=/usr/lib/wine/`wineserver'ifelse(ARCH_BITS, 64, 64)
ENV WINEPREFIX=/root/.wine
RUN sed -i 's/\(Environment,"PATH".*\)"$/\1;z:\\`mingw'ARCH_BITS\\bin"/' \
  /usr/share/wine/wine/wine.inf
RUN echo "\nwineboot --init" >> $HOME/.bashrc
ifelse(ARCH_BITS, 64, RUN ln -sf /usr/bin/wine64 /usr/bin/wine)


# Disable winemenubuilder.exe, services.exe and plugplay.exe
define(`WINE_TRIPLE', ifelse(ARCH_BITS, 64, `x86_64', `i386')-linux-gnu)
RUN TARGET_DIR=$(dirname \
  $(find /usr/lib/WINE_TRIPLE/wine -name winemenubuilder.exe | head -1)); (\
  echo "int main(int argc, char *argv[]) {return 0;}" > null.c &&\
  MINGW_CC -o $TARGET_DIR/winemenubuilder.exe null.c &&\
  MINGW_CC -o $TARGET_DIR/services.exe null.c &&\
  MINGW_CC -o $TARGET_DIR/plugplay.exe null.c)
