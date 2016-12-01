include(macros.m4)

define(`YUM', `_(RUN
  rpm --rebuilddb &&
  yum install -y --quiet `$1' &&
  rpm --query --queryformat "" `$1')')

# Install prerequisites
YUM(wget gcc gcc-c++ git scons redhat-lsb make cmake rpm-build binutils-devel
  valgrind python-twisted openssl-devel openssh-clients clang file m4 vim
  unzip gettext)

include(buildbot.m4)
