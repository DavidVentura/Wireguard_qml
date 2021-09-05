#!/bin/bash
if [ $# -ne 1 ]; then
	echo Usage: $0 filename
	echo 'with no extension. It will go to screenshots/<filename>.png'
	exit 1
fi
import -window $(wmctrl -l | grep keepass.davidv.dev | awk '{print $1}') "screenshots/$1.png"
