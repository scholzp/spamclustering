#!/bin/bash

inputDir=$1;
outputDir=$2;
callDir=$(pwd);

# check existance of source and output direcotry
if ! [ $# == 2 ]; then
	echo "More or less than two paramters detected.";
	echo "Please specify input and output directories in the follwing way:";
	echo "copyFormDirectoryTree.sh inputDirectory outputDirectory";
	return 1 2>/dev/null;
	exit 1;
fi	

find ${inputDir} -type f -exec cp {} ${outputDir} \;