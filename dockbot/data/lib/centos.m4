include(macros.m4)

define(`YUM', `_(RUN
  rpm --rebuilddb &&
  yum install -y --quiet `$1' &&
  rpm --query --queryformat "" `$1')')

YUM(wget)
include(epel.m4)

# Install prerequisites
YUM(gcc gcc-c++ git scons redhat-lsb make cmake rpm-build binutils-devel
  valgrind python-twisted openssl-devel openssh-clients file m4 unzip gettext)

include(buildbot.m4)
