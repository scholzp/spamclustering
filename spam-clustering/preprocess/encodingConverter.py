import email
import sys
import re
import base64

from mailIo import mailIo
from enum import Enum

class ContentType(Enum):
	UNDEFINED = 0
	PLAINTEXT = 1
	HTMLTEXT = 2

class Encoding(Enum):
	UNDEFINED = 0
	BASE64 = 1
	QUOTEDPRINTABLE = 2

class Payload: 
	start = 0
	end = 0
	content = None
	contentType = None
	encodingType = None
	charset = None

	def __init__(self, start, end, content, contentType, encodingType):
		self.start = start
		self.end = end
		self.content = content
		self.contentType = contentType
		self.encodingType = encodingType

	def setCharset(self, charset):
		self.charset = charset

	def decode(self):
		result = ''
		match self.encodingType:
			case Encoding.BASE64:
				result = base64.decodebytes(bytes(self.content, 'utf-8'))
		
		return result


	def __str__(self):
		result = 'This is an payload-object of an email message.\n'
		result += 'Start in mail: ' + str(self.start)
		result += '\nEnd in mail '+ str(self.end) + '\n'
		result += 'Payload:' + self.content[:10] +'[...]'
		result += self.content[len(self.content)-10:] + '\n'
		strCType = ''
		match self.contentType:
			case ContentType.PLAINTEXT:
				strCType = 'Plaintext, charset: ' + self.charset 
			case ContentType.HTMLTEXT:
				strCType = 'HTML'
			case ContentType.UNDEFINED:
				strCType = 'Undefined'

		strEType = ''
		match self.encodingType:
			case Encoding.BASE64:
				strEType = 'base64'
			case Encoding.QUOTEDPRINTABLE:
				strEType = 'quoted-printable'
			case Encoding.UNDEFINED:
				strEType = 'undefined'
		result += 'Type: ' + strCType + '\nEncoding: ' + strEType + '\n'

		return result

class ExtentedEmailMessage:
	
	serializedEmail = None
	payloadList = []

	# some pattern strings to create regular expressions from
	patternHtml = '(<html.*/html>)'
	patternBase64 = '(\n(?:[a-zA-Z0-9=]|\n)+\n)'
	patternContentTypePlain = 'Content-Type: text/plain'
	patternContentTypeHtml = 'Content-Type: text/html'
	patternTransferEncoding = 'Content-Transfer-Encoding: (.*)\n'

	def __init__(self, message):
		self.serializedEmail = message.as_string()
		self.contentList = []

	def extractPayload(self):
		matches = []
		patternList = [
			'(' + self.patternContentTypePlain+ ').*\n'
				+self.patternTransferEncoding + self.patternBase64,
			'(' + self.patternContentTypeHtml+ ').*\n'+
				self.patternTransferEncoding  + '.*\n' + self.patternHtml
		]
		matches = self.matchPatternList(patternList)
		
		for m in matches:
			self.payloadList.append(self.createPayloadFromMatch(m))


	def matchPatternList(self, patternList):
		result = []
		for pattern in patternList:
			r = re.compile(pattern, re.S)
			for m in r.finditer(self.serializedEmail):
				result.append(m)
		return result

	def createPayloadFromMatch(self, m):
		start = m.start()
		end = m.end()
		mail = self.serializedEmail
		content = m.group(3)
		contentType = self.retrieveContentType(m)
		transferEncoding = self.retrieveEncoding(m)
		payload = Payload(start, end, content, contentType, transferEncoding)
		if payload.contentType == ContentType.PLAINTEXT:
			pattern = 'charset=\"(.*)\"'
			charsetMatch = re.search(pattern, m.group(0))
			if charsetMatch:
				payload.setCharset(charsetMatch.group(1))
		return payload

	def retrieveEncoding(self, m):
		match m.group(2):
			case 'base64':
				return Encoding.BASE64
			case 'quoted-printable':
				return Encoding.QUOTEDPRINTABLE
			case _:
				return Encoding.UNDEFINED
	
	def retrieveContentType(self, m):
		match m.group(1):
			case self.patternContentTypePlain:
				return ContentType.PLAINTEXT
			case self.patternContentTypeHtml:
				return ContentType.HTMLTEXT
			case _:
				return ContentType.UNDEFINED

def main():
	argv = sys.argv
	argc = len(sys.argv)
	if argc > 0:
		print('This script was started as main for debuging purposes.')
		print('Using "', argv[1], '"as input file\n\n')
		fn = argv[1]
		message = mailIo.readMailFromEmlFile(fn)
		#print(message.as_string())
		#print(message.keys())
	#	if not (message.is_multipart()):
		extMessage = ExtentedEmailMessage(message)
		extMessage.extractPayload()
		print(extMessage.payloadList[0].decode())
	else:
		print("Path was not given")

	
if __name__ == "__main__":
	main()
