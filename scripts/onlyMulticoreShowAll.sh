#!/bin/bash

for n in `/root/scripts/nodes.sh`; do
  echo -n XXX $n XXX" "
  /root/scripts/onlyMulticoreShow.sh $n
done


