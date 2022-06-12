import sys
import re
import base64

from enum import Enum
from mailIo import mailIo


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
        match self.encoding_type:
            case Encoding.BASE64:
                result = base64.decodebytes(bytes(self.content, 'utf-8'))
        return result

    def __str__(self):
        result = 'This is an payload-object of an email message.\n'
        result += 'Start in mail: ' + str(self.start)
        result += '\nEnd in mail: ' + str(self.end) + '\n'
        result += 'Payload:' + self.content[:10] + '[...]'
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
    serialized_email = None
    payload_list = []

    # some pattern strings to create regular expressions from
    patternHtml = '(<html.*/html>)'
    patternBase64 = '(\n(?:[a-zA-Z0-9=]|\n)+\n)'
    patternContentTypePlain = 'Content-Type: text/plain'
    patternContentTypeHtml = 'Content-Type: text/html'
    patternTransferEncoding = 'Content-Transfer-Encoding: (.*)\n'

    def __init__(self, message):
        self.serialized_email = message.as_string()
        self.payload_list = []

    def extract_payload(self):
        matches = []
        pattern_list = [
            '(' + self.patternContentTypePlain + ').*\n'
                + self.patternTransferEncoding + self.patternBase64,
            '(' + self.patternContentTypeHtml + ').*\n'
                + self.patternTransferEncoding + '.*\n' + self.patternHtml
        ]
        matches = self._match_pattern_list(pattern_list)
        for m in matches:
            self.payload_list.append(self._create_payload_from_match(m))

    def _match_pattern_list(self, pattern_list):
        result = []
        for pattern in pattern_list:
            r = re.compile(pattern, re.S)
            for m in r.finditer(self.serialized_email):
                result.append(m)
        return result

    def _create_payload_from_match(self, m):
        start = m.start()
        end = m.end()
        content = m.group(3)
        content_type = self._retrieve_content_type(m)
        transfer_encoding = self._retrieve_encoding(m)
        payload = Payload(start, end, content, content_type, transfer_encoding)
        if payload.content_type == ContentType.PLAINTEXT:
            pattern = 'charset=\"(.*)\"'
            charset_match = re.search(pattern, m.group(0))
            if charset_match:
                payload.set_charset(charset_match.group(1))
        return payload

    def _retrieve_encoding(self, m):
        match m.group(2):
            case 'base64':
                return Encoding.BASE64
            case 'quoted-printable':
                return Encoding.QUOTEDPRINTABLE
            case _:
                return Encoding.UNDEFINED

    def _retrieve_content_type(self, m):
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
    #   if not (message.is_multipart()):
        extMessage = ExtentedEmailMessage(message)
        extMessage.extract_payload()
        print(extMessage.payload_list[0].decode())
    else:
        print("Path was not given")


if __name__ == "__main__":
    main()
