define(`MINGW_BITS', ARCH_BITS)
define(`MINGW_ARCH', ifelse(MINGW_BITS, 64, `x86_64', `i686'))
define(`MINGW_DEB_ARCH', translit(MINGW_ARCH, `_', `-'))
define(`MINGW_ROOT', `/mingw'ARCH_BITS)
define(`MINGW_PREFIX', MINGW_ARCH-w64-mingw32-)
define(`MINGW_CC', /usr/bin/MINGW_PREFIX`gcc')
define(`MINGW_CXX', /usr/bin/MINGW_PREFIX`g++')

APT(gcc-mingw-w64-MINGW_DEB_ARCH g++-mingw-w64-MINGW_DEB_ARCH libarchive-dev
  libcurl4-openssl-dev libgpgme11-dev dirmngr)

include(pacman.m4)

# Configure pacman for mingw
define(`PACMAN_KEY', 5F92EFC1A47D45A1)
RUN echo "\n\
[`mingw'MINGW_BITS]\n\
SigLevel = Required\n\
Server = http://repo.msys2.org/mingw/MINGW_ARCH" >> /etc/pacman.conf
RUN pacman-key --init &&\
  dirmngr </dev/null &&\
  pacman-key -r PACMAN_KEY &&\
  pacman-key --lsign-key PACMAN_KEY &&\
  pacman --noconfirm -Sy --force --asdeps

# Install mingw packages with pacman
define(`PACMAN_PREFIX', mingw-w64-MINGW_ARCH)
PACMAN(PACMAN_PREFIX-openssl PACMAN_PREFIX-python2 PACMAN_PREFIX-gcc)

ENV PATH=MINGW_ROOT/bin:$PATH
