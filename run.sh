#!/bin/sh
set -e
ip=192.168.2.155
ip=192.168.2.156
clickable build   --arch arm64 --skip-review --ssh $ip
clickable install --arch arm64 --ssh $ip
clickable launch  --arch arm64 --ssh $ip
clickable logs    --arch arm64 --ssh $ip
