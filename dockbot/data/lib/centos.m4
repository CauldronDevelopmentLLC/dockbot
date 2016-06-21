# Create yum install script
RUN echo -e "#!/bin/bash\n\
rpm --rebuilddb && \n\
yum install -y --quiet \$@ && \n\
rpm --query --queryformat "" \$@" > /usr/bin/yum-install && \
chmod +x /usr/bin/yum-install

# Install prerequisites
RUN yum-install wget gcc gcc-c++ git scons redhat-lsb make cmake rpm-build \
  binutils-devel valgrind python-twisted openssl-devel openssh-clients clang
