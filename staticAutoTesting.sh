#!/bin/bash

APP_PATH="/test_apps/"
ANALYSIS_PATH="/bbnAnalysis"
INPUT_DIR="/bbnAnalysis/apks"

APKEXT=.apk

cd $ANALYSIS_PATH

echo "Begin statically analyzing all the $APKEXT files in INPUT DIRECTORY ($INPUT_DIR)!!"

for file in $APP_PATH/*$APKEXT
do
	echo "Analyzing $file"

	rm -rf $INPUT_DIR/*
	cp $file $INPUT_DIR/

	filename=$(basename $file)
	file=$(basename $file $APKEXT)
	./resourceAnalysis.sh $file ${file}dir $INPUT_DIR $APKEXT 24
done
