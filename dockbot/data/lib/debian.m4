# Make apt-get retry downloads
RUN echo 'Acquire::Retries "5";' > /etc/apt/apt.conf.d/50retry

# Install prerequisites
RUN apt-get update && \
  apt-get install -y --no-install-recommends wget git scons \
  build-essential binutils-dev fakeroot valgrind python-twisted-core \
  debian-keyring debian-archive-keyring ca-certificates libssl-dev \
  openssh-client apt-utils
