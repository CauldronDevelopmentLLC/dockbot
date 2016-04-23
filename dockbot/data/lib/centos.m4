# Install prerequisites
ENV YUM_PKGS wget gcc gcc-c++ git scons redhat-lsb make cmake binutils-devel \
  valgrind python-twisted openssl-devel openssh-clients rpm-build clang

RUN yum install -y --quiet $YUM_PKGS
RUN rpm --query --queryformat "" $YUM_PKGS
