#!/bin/bash

if [ $# != 1 ]; then
  echo Give a node
  exit 1
fi

node=$1
condor_config_val -verbose -name $node -startd -set "OnlyMulticore = False"
condor_reconfig $node
condor_reconfig -daemon startd $node

