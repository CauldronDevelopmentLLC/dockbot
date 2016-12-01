define(`CXFREEZE_VERSION', ifdef(`CXFREEZE_VERSION', CXFREEZE_VERSION, 4.3.4))
define(`CXFREEZE_BASE', cx_Freeze-CXFREEZE_VERSION)
define(`CXFREEZE_PKG', CXFREEZE_BASE.tar.gz)

WGET(https://pypi.python.org/packages/source/c/cx_Freeze/CXFREEZE_PKG)

RUN tar xf CXFREEZE_PKG &&\
  cd CXFREEZE_BASE &&\
  touch cxfreeze-postinstall &&\
  sed -i 's/[xX]86/amd64/g' source/bases/manifest.txt &&\
  wine MINGW_ROOT/bin/python2.exe setup.py install &&\
  cd .. &&\
  rm -rf CXFREEZE_PKG CXFREEZE_BASE &&\
  rm -rf $HOME/.wine # wine config is messed up after this
