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
    patternBase64 = '\n((?:[a-zA-Z0-9=]|\n)+)\n'
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
        result = 'This is an ExtendedEmailMessage object. \n'
        if self.mail_from:
            result += 'From        : ' + self.mail_from + '\n'
        if self.mail_sender:
            result += 'Sender      : ' + self.mail_sender + '\n'
        if self.mail_to:
            result += 'To          : ' + self.mail_to + '\n'
        if self.mail_subject:
            result += 'Subject     : ' + self.mail_subject + '\n'
        if self.mail_thread_topic:
            result += 'Thread-Topic: ' + self.mail_thread_topic + '\n'
        result += 'It contains the following payloads:\n'
        for payload in self.payload_list:
            result += str(payload)
            result += '-----------------------------------------------------\n'
        return result

class MailAnonymizer:
    extended_mail = None

    def __init__(self, extended_mail):
        self.extended_mail = extended_mail

    def anonymize(self):
        print(self.extended_mail)
        fake = Faker()
        mail_to = self.extended_mail.mail_to
        from_dict = self._split_from_into_word_list(mail_to)
        self._find_replacements(from_dict)
        print(self.extended_mail)
        self._anonymize_payload(from_dict)
        #print(self.extended_mail)

    def _anonymize_payload(self, replacement_dict):
        for payload in self.extended_mail.payload_list:
            print(payload)
            if (payload.content_type == ContentType.PLAINTEXT) or \
               (payload.content_type == ContentType.HTMLTEXT):
                string = payload.to_utf8()
                for key in replacement_dict.keys():
                    string = string.replace(key, replacement_dict[key])
        payload.set_text_content(string)

    def _find_replacements(self, key_list):
        fake = Faker()
        for key in key_list:
            new_value = ''
            match key_list[key]:
                case 'name':
                    new_value = fake.first_name()
                case 'email':
                    new_value = fake.ascii_safe_email()
            key_list.update({key: new_value})


    def _split_from_into_word_list(self, from_string):
        result = dict()
        # first convert to lower case
        string = from_string.lower()
        # Use the following regex to find name and/or email address of the
        # recipient. The regex recognises one of the follwing three patterns:
        #   form of header | pattern
        #   ---------------+-----------------------
        #   name only      | "surename, forename "
        #   email only     | <mail.address@domain.second.example>
        #   email and name | "forename surename" <mail@domain.example>
        #
        # Mail addresses can contain an unspecified number of subdomains. Names
        # must consist of at least two words. Both can contain alphanumeric
        # characters. If the name part matches, a group with id 'name' will be
        # returned by the match object. Analog with the email pattern, of which
        # the id is 'email'.
        regexp = re.compile(r"""
            (?:"?
                (?P<name>              # assign group name 'name'
                    \w+,?(?:\s\w+)+    # match fore-and lastname
                )                      # can be comma serpated
            "?)?                       # omit if only mail is to be matched
            \s?                        # space between mail adress and name
            (?:<?
                (?P<email>             # asssign group name 'email'
                    \w+(\.?\w+)*@\w+(?:\.\w+)+  # match email
                )
             >?)?                      # omit if only name is to be matched
            """, re.X)
        match_result = regexp.search(string)

        # create a list of potential word which should be replaced
        match_group_keys = ['name', 'email']
        for key in match_group_keys:
            group_result = match_result.groupdict()[key]
            if group_result:
                for word in group_result.split():
                    result[word.rstrip(',')] = key

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
        anonymizer = MailAnonymizer(extMessage)
        anonymizer.anonymize()
    else:
        print("Path was not given")


if __name__ == "__main__":
    main()
