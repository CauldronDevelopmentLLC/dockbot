# Install EPL
ADD https://dl.fedoraproject.org/pub/epel/epel-release-latest-5.noarch.rpm .
RUN rpm -i --quiet epel-release-latest-5.noarch.rpm
