import email
import os

from email.iterators import _structure
from email import parser
from email import policy

def writeMessageToEml(message, fn):
	if fn and fn != '':
		with open(fn, 'w') as out:
			gen = email.generator.Generator(out)
			gen.flatten(message)

def readMailFromEmlFile(path):
	"""Return an EmailMessage object obtained from a file
	keyword arguments:
	path -- path of the file to read and create a message from 
	"""
	result = None
	if os.path.isfile(path):
		with open(path, 'r') as fp:
			# Use policy.default for creating a EmailMessage factory instead of
			# a message factory
			parser = email.parser.Parser(policy=email.policy.default)
			message = parser.parse(fp)
			result = message
	else:
		print("Error: File does not exists!")
	return result
