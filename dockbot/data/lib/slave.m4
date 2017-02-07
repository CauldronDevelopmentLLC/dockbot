WORKDIR /host

RUN echo "alias ls='ls --color'" >> $HOME/.bashrc

ENV PATH=/host/bin:$PATH

ENTRYPOINT \
  if [ -e $HOME/.bashrc ]; then . $HOME/.bashrc; fi && \
  twistd --pidfile= -ny slave.tac
