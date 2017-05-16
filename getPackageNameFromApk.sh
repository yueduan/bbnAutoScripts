#!/bin/bash

apk=$1

/home/yduan/yueduan/android-5.0.0_r3/out/host/linux-x86/bin/aapt dump badging $apk | awk -v FS="'" '/package: name=/{print $2}'

