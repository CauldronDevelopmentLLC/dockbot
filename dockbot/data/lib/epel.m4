define(`EPEL_VERSION', ifdef(`EPEL_VERSION', EPEL_VERSION, 6))
define(`EPEL_PKG', epel-release-latest-EPEL_VERSION.noarch.rpm)

WGET(https://dl.fedoraproject.org/pub/epel/EPEL_PKG)
RUN rpm -i --quiet EPEL_PKG
RUN sed -i "s/mirrorlist=https/mirrorlist=http/" /etc/yum.repos.d/epel.repo
