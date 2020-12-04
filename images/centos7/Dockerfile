FROM registry.centos.org/centos:7

ARG foreman_version

RUN yum -y install http://yum.theforeman.org/client/$foreman_version/el7/x86_64/foreman-client-release.rpm

RUN yum -y install subscription-manager

CMD /sbin/init
