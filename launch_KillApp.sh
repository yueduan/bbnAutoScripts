#!/bin/bash

apk=$1
launch=$2

packageName=$(/home/yduan/yueduan/android-5.0.0_r3/out/host/linux-x86/bin/aapt dump badging $apk | awk -v FS="'" '/package: name=/{print $2}')

echo "Package Name: $packageName"
if [ "$launch" = "1" ]
then
	adb shell monkey -p $packageName -c android.intent.category.LAUNCHER 1
elif [ "$launch" = "2" ]
then
	adb shell ps | grep $packageName | awk '{print $2}' | xargs adb shell kill
fi
