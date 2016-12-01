RUN mv /bin/uname /bin/uname.orig &&\
  echo '#!/bin/sh' > /bin/uname &&\
  echo '/usr/bin/linux32 /bin/uname.orig "$@"' >> /bin/uname &&\
  chmod +x /bin/uname &&\
  uname -a
