import base64
import quopri

from enum import Enum

class ContentType(Enum):
    ''' Enum type to denote content type of a mail's payload
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
    """ Helper class to store payload information.

    Content of each part of an email is viewed as one payload. The payload
    class contains this (encoded) content and offers functionality to modify
    the content. Moreover the position in the serialized mail is stored, so
    later an in place replacement can be done.

    :param start: Index of the first character of this payload in the source
        mail
    :type start: int
    :param end: Index of the last character of this payload in the source
        mail
    :type start: int
    :param content: Content of the payload.
    :type content: str
    :param content_type: MIME type of the content.
    :type: :class:`spamclustering.preprocess.encodingConverter.ContentType`
    :param content_type: Transfer encoding of the mail
    :type: :class:`spamclustering.preprocess.encodingConverter.Encoding`
    """

    def __init__(self, start, end, content, content_type, encoding_type):
        self.start = start
        self.end = end
        self.content = content
        self.content_type = content_type
        self.encoding_type = encoding_type
        self.charset = 'utf-8'

    def set_charset(self, charset):
        """Set the char set of the content of this payload.

        :param charset: Character set of the text content, represented as a
            python codec string.
        :type charset: str
        """
        self.charset = charset

    def decode(self):
        """ Use the transfer encoding information to decode the content.

        :return: Returns an array of bytes representing the decoded content.
        :rtype: str
        """
        result = ''
        match self.encoding_type:
            case Encoding.BASE64:
                content_bytes = bytes(self.content, 'utf-8')
                result = base64.decodebytes(content_bytes)
            case Encoding.QUOTEDPRINTABLE:
                result = quopri.decodestring(self.content)
            case _:
                result = bytes(self.content, 'utf-8')
        return result

    def do_transfer_encoding(self, content_bytes):
        """ Use the transfer encoding information to encode the given content.
        This function will not overwrite the content stored in this class.

        :param content_bytes: Bytes array containing the content to encode.
        :type content_bytes: bytes
        :return: Encoded content
        :rtype: bytes
        """
        result = ''
        match self.encoding_type:
            case Encoding.BASE64:
                result = base64.encodebytes(content_bytes)
            case Encoding.QUOTEDPRINTABLE:
                result = quopri.encodestring(content_bytes)
            case _:
                result = content_bytes
        return result

    def to_utf8(self):
        """ Return the content stored in by this object as a UTF-8 string.
        The content stored by this class is first decoded with respect to the
        transfer encoding. In the next step the resulting bytes stream is
        decoded from the respective character set into UTF-8 for python usage.

        :return: An UTF-8 formatted string.
        :rtype: str
        """
        result = None
        content_bytes = self.decode()
        match self.content_type:
            case ContentType.PLAINTEXT:
                result = content_bytes.decode(self.charset, 'ignore')
            case ContentType.HTMLTEXT:
                result = content_bytes.decode(self.charset, 'ignore')
        return result

    def set_text_content(self, text):
        """ Overwrites the content stored by this object with the given text.
        The given text will first encoded into the target character set and
        then the original transfer encoding will be performed. The result is
        then used to overwrite the content stored by this object.

        :param text: String used to replace the content.
        :type: str
        """
        # first encode the text into the original char set
        content = ''
        match self.content_type:
            case ContentType.PLAINTEXT:
                content = bytes(text.encode(self.charset))
                content = self.do_transfer_encoding(content)
                self.content = str(content, self.charset)
            case ContentType.HTMLTEXT:
                content = bytes(text.encode(self.charset))
                content = self.do_transfer_encoding(content)
                self.content = str(content, self.charset)

    def __str__(self):
        """ Return a string describing the payload and it's content.
        """

        result = 'This is an payload-object of an email message.\n'
        result += 'Start in mail: ' + str(self.start)
        result += '\nEnd in mail: ' + str(self.end) + '\n'
        result += 'Payload:\n' + self.content[:10] + '[...]'
        result += self.content[len(self.content) - 10:] + '\n'
        str_c_type = ''
        match self.content_type:
            case ContentType.PLAINTEXT:
                str_c_type = 'Plain text, char set: ' + self.charset
            case ContentType.HTMLTEXT:
                str_c_type = 'HTML, char set: ' + self.charset
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
