# Install EPL
ADD https://dl.fedoraproject.org/pub/epel/epel-release-latest-6.noarch.rpm .
RUN rpm -i --quiet epel-release-latest-6.noarch.rpm
