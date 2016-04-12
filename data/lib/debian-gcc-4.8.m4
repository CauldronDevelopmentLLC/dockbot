RUN apt-get install -y --no-install-recommends libgcc-4.8-dev gcc-4.8 g++-4.8

RUN update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-4.8 10 && \
  update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-4.8 10 && \
  update-alternatives --install /usr/bin/cc cc /usr/bin/gcc 30 && \
  update-alternatives --install /usr/bin/c++ c++ /usr/bin/g++ 30 && \
  update-alternatives --set gcc /usr/bin/gcc-4.8 && \
  update-alternatives --set g++ /usr/bin/g++-4.8 && \
  update-alternatives --set cc /usr/bin/gcc && \
  update-alternatives --set c++ /usr/bin/g++
