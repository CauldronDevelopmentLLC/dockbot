WORKDIR /host

ENV PATH=/host/bin:$PATH

ENTRYPOINT \
  if [ -e $HOME/.bashrc ]; then . $HOME/.bashrc; fi && \
  twistd --pidfile= -ny slave.tac
