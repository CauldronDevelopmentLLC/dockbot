# Install buildbot 0.7.10p2-jcoffland
RUN git clone -b 0.7.10p2-jcoffland --depth=1 \
  https://github.com/CauldronDevelopmentLLC/buildbot
RUN cd buildbot && python setup.py install && cd .. && rm -rf buildbot
