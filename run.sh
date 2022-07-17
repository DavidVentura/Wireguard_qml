#!/bin/sh
set -e
ip=192.168.2.179
arch=armhf
cd daemon && GOARCH=$(echo $arch | sed 's/armhf/arm/') CGO_ENABLED=0 go build -o daemon -ldflags "-s -w"
clickable build   --arch $arch --skip-review --ssh $ip
clickable install --arch $arch --ssh $ip
clickable launch  --arch $arch --ssh $ip
clickable logs    --arch $arch --ssh $ip
