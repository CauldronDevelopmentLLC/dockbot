include(macros.m4)

define(`APT',
  RUN apt-get update && apt-get install -y --no-install-recommends `_(`$1')')

# Make apt-get retry downloads
RUN echo 'Acquire::Retries "5";' > /etc/apt/apt.conf.d/50retry

# Install prerequisites
APT(wget git subversion scons build-essential binutils-dev fakeroot cmake less
  valgrind python-twisted-core debian-keyring debian-archive-keyring file m4 vim
  ca-certificates libssl-dev openssh-client apt-utils pkg-config unzip gettext)

include(buildbot.m4)
