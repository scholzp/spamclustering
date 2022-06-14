import sys
import re
import base64
import quopri

from enum import Enum
from mailIo import mailIo
from faker import Faker

class ContentType(Enum):
    ''' Enum type to denote content type of a mails payload
    '''
    UNDEFINED = 0
    PLAINTEXT = 1
    HTMLTEXT = 2


class Encoding(Enum):
    '''Enum type to denote the transfer encoding used for the respective
    payload
    '''
    UNDEFINED = 0
    BASE64 = 1
    QUOTEDPRINTABLE = 2


class Payload:
    start = 0
    end = 0
    content = None
    content_type = None
    encoding_type = None
    charset = None

    def __init__(self, start, end, content, content_type, encoding_type):
        self.start = start
        self.end = end
        self.content = content
        self.content_type = content_type
        self.encoding_type = encoding_type

    def set_charset(self, charset):
        self.charset = charset

    def decode(self):
        result = ''
        content_bytes = bytes(self.content, 'utf-8')
        print('Decode:', content_bytes)
        match self.encoding_type:
            case Encoding.BASE64:
                result = base64.decodebytes(content_bytes)
            case Encoding.QUOTEDPRINTABLE:
                result = quopri.decodestring(content_bytes)
        return result

    def do_transfer_encoding(self, content_bytes):
        result = ''
        print(content_bytes)
        match self.encoding_type:
            case Encoding.BASE64:
                result = base64.encodebytes(content_bytes)
            case Encoding.QUOTEDPRINTABLE:
                result = quopri.encodestring(content_bytes)
        return result

    def to_utf8(self):
        result = None
        content_bytes = self.decode()
        match self.content_type:
            case ContentType.PLAINTEXT:
                result = content_bytes.decode(self.charset, 'ignore')
            case ContentType.HTMLTEXT:
                result = content_bytes.decode('utf-8', 'ignore')
        return result

    def set_text_content(self, text):
        # first encode the text into the original charset
        content = ''
        match self.content_type:
            case ContentType.PLAINTEXT:
                content = bytes(text.encode(self.charset))
                content = self.do_transfer_encoding(content)
                self.content = str(content, self.charset)
            case ContentType.HTMLTEXT:
                content = bytes(text.encode('utf-8'))
                content = self.do_transfer_encoding(content)
                self.content = str(content, 'utf-8')

    def __str__(self):
        result = 'This is an payload-object of an email message.\n'
        result += 'Start in mail: ' + str(self.start)
        result += '\nEnd in mail: ' + str(self.end) + '\n'
        result += 'Payload:\n' + self.content[:10] + '[...]'
        result += self.content[len(self.content) - 10:] + '\n'
        str_c_type = ''
        match self.content_type:
            case ContentType.PLAINTEXT:
                str_c_type = 'Plaintext, charset: ' + self.charset
            case ContentType.HTMLTEXT:
                str_c_type = 'HTML'
            case ContentType.UNDEFINED:
                str_c_type = 'Undefined'

        str_e_type = ''
        match self.encoding_type:
            case Encoding.BASE64:
                str_e_type = 'base64'
            case Encoding.QUOTEDPRINTABLE:
                str_e_type = 'quoted-printable'
            case Encoding.UNDEFINED:
                str_e_type = 'undefined'
        result += 'Type: ' + str_c_type + '\nEncoding: ' + str_e_type + '\n'

        return result


class ExtentedEmailMessage:
    email_message = None
    payload_list = []
    mail_from = None
    mail_to = None
    mail_sender = None
    mail_subject = None
    mail_thread_topic = None

    # some pattern strings to create regular expressions from
    patternHtml = '(<html.*/html>)'
    patternBase64 = '((?:[a-zA-Z0-9=]|\n)+)\n'
    patternContentTypePlain = 'Content-Type: text/plain'
    patternContentTypeHtml = 'Content-Type: text/html'
    patternTransferEncoding = 'Content-Transfer-Encoding: '
    pattern_encoding_types = '(base64|quoted-printable)\n'

    def __init__(self, message):
        self.email_message = message
        self.payload_list = []

        self.mail_from = message.get('From')
        self.mail_to = message.get('To')
        self.mail_sender = message.get('Sender')
        self.mail_subject = message.get('Subject')
        self.mail_thread_topic = message.get('Thread-Topic')

    def extract_payload(self):
        matches = []
        pattern_list = [
            '(' + self.patternContentTypePlain + ').*\n'
                + self.patternTransferEncoding
                + self.pattern_encoding_types
                + '(?:.*:.*\n)?' + self.patternBase64,
            '(' + self.patternContentTypeHtml + ').*\n'
                + self.patternTransferEncoding
                + self.pattern_encoding_types
                + '.*\n' + self.patternHtml
        ]
        matches = self._match_pattern_list(pattern_list)
        for match_obj in matches:
            self.payload_list.append(
                self._create_payload_from_match(match_obj))

    def _match_pattern_list(self, pattern_list):
        result = []
        serialized_email = self.email_message.as_string()
        for pattern in pattern_list:
            regexp = re.compile(pattern, re.S)
            for match_obj in regexp.finditer(serialized_email):
                result.append(match_obj)
        return result

    def _create_payload_from_match(self, match_obj):
        start = match_obj.start()
        end = match_obj.end()
        content = match_obj.group(3)
       # print(content)
        content_type = self._retrieve_content_type(match_obj)
        transfer_encoding = self._retrieve_encoding(match_obj)
        payload = Payload(start, end, content, content_type, transfer_encoding)
        if payload.content_type == ContentType.PLAINTEXT:
            pattern = 'charset=\"(.*)\"'
            charset_match = re.search(pattern, match_obj.group(0))
            if charset_match:
                payload.set_charset(charset_match.group(1))
        return payload

    def _retrieve_encoding(self, match_obj):
        match match_obj.group(2):
            case 'base64':
                return Encoding.BASE64
            case 'quoted-printable':
                return Encoding.QUOTEDPRINTABLE
            case _:
                return Encoding.UNDEFINED

    def _retrieve_content_type(self, match_obj):
        match match_obj.group(1):
            case self.patternContentTypePlain:
                return ContentType.PLAINTEXT
            case self.patternContentTypeHtml:
                return ContentType.HTMLTEXT
            case _:
                return ContentType.UNDEFINED

    def __str__(self):
        result = 'This is an ExtendedMail object. \n'
        result += 'It contains the following payloads:\n'
        for payload in self.payload_list:
            result += str(payload)
            result += '-----------------------------------------------------\n'
        return result

def main():
    argv = sys.argv
    argc = len(sys.argv)
    if argc > 0:
        print('This script was started as main for debuging purposes.')
        print('Using "', argv[1], '"as input file\n\n')
        fn = argv[1]
        message = mailIo.readMailFromEmlFile(fn)
    #   if not (message.is_multipart()):
        extMessage = ExtentedEmailMessage(message)
        extMessage.extract_payload()
        #print(extMessage)
        print(extMessage.payload_list[0].to_utf8())
    else:
        print("Path was not given")


if __name__ == "__main__":
    main()
