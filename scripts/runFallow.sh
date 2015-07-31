#!/bin/bash

ps | grep $0 | grep -v grep > /var/tmp/$0.pid
pids=$(cat /var/tmp/$0.pid | cut -d ' ' -f 1)
for pid in $pids
do
   if [ $pid -ne $$ ]; then
      echo " $0 is already running. Exiting"
      exit 7
   fi
done
rm -f /var/tmp/$0.pid

prog="fallow"
lockfile=/var/lock/subsys/$prog

cd /root/scripts/
while [ 1 ]; do
  ./fallow.py -s 300

  for n in `seq 1 100`; do
    if [ ! -f $lockfile ] ; then
      exit
    fi
    sleep 3
  done
done >> fallow.log

