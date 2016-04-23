WORKDIR /host

ENTRYPOINT \
  if [ -e $HOME/.bashrc ]; then . $HOME/.bashrc; fi && \
  export NCORES=$(grep -c ^processor /proc/cpuinfo) && \
  export SCONS_JOBS=$NCORES && \
  rm -f twistd.pid && \
  twistd -l slave.log -ny slave.tac && \
  tail -f twistd.log
