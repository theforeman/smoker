FROM registry.centos.org/centos:6

ARG foreman_version

RUN rm -f /etc/yum.repos.d/*
ADD centos-6-vault.repo /etc/yum.repos.d/centos-6-vault.repo
ADD epel-subscription-manager.repo /etc/yum.repos.d/epel-subscription-manager.repo
RUN yum -y install https://archives.fedoraproject.org/pub/archive/epel/6/x86_64/epel-release-6-8.noarch.rpm
RUN yum -y install http://yum.theforeman.org/client/$foreman_version/el6/x86_64/foreman-client-release.rpm

RUN yum -y clean all && yum -y install upstart subscription-manager

CMD /sbin/init
