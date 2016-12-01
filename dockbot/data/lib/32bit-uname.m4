RUN mv /bin/uname /bin/uname.orig && \
  echo '#!/bin/sh\n/usr/bin/linux32 /bin/uname.orig "$@"' > /bin/uname && \
  chmod +x /bin/uname
