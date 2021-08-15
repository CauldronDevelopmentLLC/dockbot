define(`CENTOS_VERSION', ifdef(`CENTOS_VERSION', CENTOS_VERSION, 6))

RUN yum install -y --quiet https://centos`'CENTOS_VERSION.iuscommunity.org/ius-release.rpm
