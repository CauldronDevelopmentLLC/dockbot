define(`PACMAN_VERSION', 5.0.1)
define(`PACMAN_BASE', pacman-PACMAN_VERSION)
define(`PACMAN_PKG', PACMAN_BASE.tar.gz)

WGET(https://sources.archlinux.org/other/pacman/PACMAN_PKG)

RUN tar xf PACMAN_PKG &&\
  cd PACMAN_BASE &&\
  ./configure --prefix=/ &&\
  make -j CONCURRENCY &&\
  make install &&\
  cd .. &&\
  rm -rf PACMAN_PKG PACMAN_BASE

define(`PACMAN', RUN pacman --noconfirm -S `_(`$1')')
