#!/bin/bash
#
# Install and set up consul to run server for tests
#
set -ev

CONSUL_VER=0.5.0
CONSUL_DL_URL=https://dl.bintray.com/mitchellh/consul/${CONSUL_VER}_linux_amd64.zip

curl -L $CONSUL_DL_URL > consul.zip
unzip -o consul.zip -d $PWD/bin/
chmod +x $PWD/bin/consul

export PATH=$PATH:$PWD/bin

# DC1
consul agent --server=true --bootstrap-expect=1 --data-dir=$PWD/ci/consul/dc1 &

sleep 5

consul agent --server=true --bootstrap-expect=1 --data-dir=$PWD/ci/consul/dc2 --config-file=$PWD/ci/consul/dc2/config.json &

sleep 5

# vim: ft=sh:
