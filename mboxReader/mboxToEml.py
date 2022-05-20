import mailbox
import email
import time
import hashlib
import os
import re 

from optparse import OptionParser
from datetime import datetime
from email.iterators import _structure

def generateMailId(message):
	mailId = str(message['Message-ID']).encode('ascii')
	hashOfId = ''
	if not mailId:
		return None

	mailTo = str(message['To']).encode('ascii')
	if not mailTo:
		return None

	hashOfId = hashlib.md5(mailId + mailTo).hexdigest()

	return hashOfId

def generateEmlFileName(message):
	id = generateMailId(message)
	inputFormat = '%a, %d %b %Y %H:%M:%S %z'
	if (not message['Date']) or (not id):
		return None
	mailDate = message['Date']
	regexp = re.compile(' \(.+\)')
	mailDate =  re.sub(regexp, '', mailDate)
	mailDate = datetime.strptime(mailDate, inputFormat)
	date = mailDate.strftime('%Y-%m-%d-%H:%M:%S')
	
	return date+'_'+id+'.eml'

def writeMessageToEml(message, fn):
	if fn and fn != '':
		with open(fn, 'w') as out:
			gen = email.generator.Generator(out)
			gen.flatten(message)

def processMbox(inPath, outPath):	
	(_, tail) = os.path.split(inPath)
	(_, dirName) = os.path.split(tail)
	outDir = outPath + '/' + dirName
	if os.path.exists(outDir):
		if not os.path.isdir(outDir):
			print("Error:", outDir, " already exists, but isn't directory!")
			print("       Aborting...")
			return -1
		else:
			print("Warning: Using already existing directory", outDir)
	else:
		print("Create ", outDir)
		os.makedirs(outDir)
	
	for message in mailbox.mbox(inPath):
		fn = generateEmlFileName(message)
		fn = outDir + '/' + fn
		writeMessageToEml(message, fn)

def main():
	usage = "usage %prog [options] arg"
	parser = OptionParser(usage)
	parser.add_option("-i", "--input", dest="ifFilename", 
					help="Specifies file to process")
	parser.add_option("-o", "--output", dest="ofFilename", 
					help="Specifies directory to write results to") 
	parser.add_option("-d", "--directory", dest="isDir", 
					help="Specifies if input is a directoy."+
					"If set, the program will process all files" +
					"in the directory. Not recursive, no subdirectories"+
					"will be searched.", default="False")

	(opts, args) = parser.parse_args()
	inFile = opts.ifFilename
	ofFile = opts.ofFilename
	isDir  = opts.isDir
	
	fileList = list()

	if not os.path.isfile(inFile):
		print("Error: File", inFile, "does not exist or is an directory.",
			"Inlcude -d switch if it's a directoy")
		return 1

	if os.path.isdir(ofFile):
		print("Warning: ", ofFile, "does already exist")

	if isDir == "True":
		print("Process dir")
		print("Not implemented yet! Run for each file without -d switch!")
		return 0
	elif isDir == "False":
		processMbox(inFile, ofFile)

if __name__ == "__main__":
	 main()
