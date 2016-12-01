APT(nsis)

# Install NSIS plugins (must be x86 versions, installer exe is 32-bit)
WGET(http://nsis.sourceforge.net/mediawiki/images/4/4a/AccessControl.zip)
RUN unzip AccessControl.zip Plugins/AccessControl.dll -d /usr/share/nsis &&\
  rm AccessControl.zip

WGET(http://nsis.sourceforge.net/mediawiki/images/c/c9/Inetc.zip)
RUN unzip -p Inetc.zip Plugins/x86-unicode/INetC.dll > \
    /usr/share/nsis/Plugins/INetC.dll &&\
  rm Inetc.zip
