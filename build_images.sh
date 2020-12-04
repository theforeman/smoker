#!/bin/bash -e

foreman_version=$1

if [[ -z $foreman_version ]] ; then
  echo "Usage: $0 FOREMAN_VERSION"
  exit 1
fi

podman build images/centos8 -t smoker-test/centos8:$foreman_version --build-arg foreman_version=$foreman_version
podman build images/centos7 -t smoker-test/centos7:$foreman_version --build-arg foreman_version=$foreman_version
podman build images/centos6 -t smoker-test/centos6:$foreman_version --build-arg foreman_version=$foreman_version
