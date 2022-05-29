import email

from email.iterators import _structure

def writeMessageToEml(message, fn):
	if fn and fn != '':
		with open(fn, 'w') as out:
			gen = email.generator.Generator(out)
			gen.flatten(message)