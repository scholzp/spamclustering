#!/bin/bash

inputDir=$1;
outputDir=$2;
callDir=$(pwd);

# check existance of source and output direcotry
if ! [ $# == 2 ]; then
	echo "More or less than two paramters detected.";
	echo "Please specify input and output directorie in the follwing way:";
	echo "readPstDirectory.sh inputDirectory outputDirectory";
	return 1 2>/dev/null;
	exit 1;
fi	

if ! [ -d "$inputDir" ]; then
	echo "Input path does not exist! Abort."
	# if input dir doesn't exist, we abort
	return 1 2>/dev/null;
	exit 1; 
fi

if ! [ -d "$outputDir" ]; then
	echo "Output directory does not exists.";
	# if output dir does not exist, we create it
	echo "Trying to create ${outputDir}";
	mkdir ${outputDir};
fi

# create a list of files to process located in inputDir
cd "${inputDir}"
fileList=$(ls *.pst);

# change back to working dir
cd "${callDir}"
for file in ${fileList}; do
	echo "Processing ${file} ...";
	#we'll name the individual output directories similar to the source
	#pst files. Remove pst file ending for this purpose.
	target=$(echo ${file} | sed 's/\.pst//');
	targetDir="$outputDir/$target";
	#readpst requieres the existance of the output dir
	mkdir -p "$targetDir";
	readpst -o "$targetDir" "$inputDir$file";
done
