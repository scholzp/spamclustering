import sys
import re
import base64
import quopri
import email
import os

from enum import Enum
from mailIo import mailIo
from faker import Faker


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
    """
    start = 0
    end = 0
    content = None
    content_type = None
    encoding_type = None
    charset = 'utf-8'

    def __init__(self, start, end, content, content_type, encoding_type):
        self.start = start
        self.end = end
        self.content = content
        self.content_type = content_type
        self.encoding_type = encoding_type

    def set_charset(self, charset):
        """Set the char set of the content of this payload.
        """
        self.charset = charset

    def decode(self):
        """ Use the transfer encoding information to decode the content.

        Returns an array of bytes representing the decoded content.
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

        Key arguments:
        content_bytes -- Bytes array containing the content to encode.

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

        Returns: An UTF-8 formatted string.
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

        Key arguments:
        text -- String used to replace the content.
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


class ExtentedEmailMessage:
    """ Adds additional modification functions to python EmailMessage.

    This class add a more complex payload/content part detection to python
    EmailMessage class.
    """
    email_message = None
    payload_list = []

    header_dict = {
        'From': None,
        'To': None,
        'Sender': None,
        'Subject': None,
        'Thread-Topic': None
    }

    # some pattern strings to create regular expressions from
    # Because of bad design decisions the html pattern contains a pattern for
    # quoted printable encoded and plain text. TODO: rework all regular
    # expression to split the task of searching for payload and header data
    patternHtml = '(?P<Content>(<html(?:.|\s)*/html>)|' + \
                  '(<=?\s?h=?\s?t=?\s?m=?\s?l=?\s?>(?:.\s)*' + \
                  '/=?\s?h=?\s?t=?\s?m=?\s?l=?\s?>))'
    patternBase64 = '\n(?P<Content>(?:(?:(?:[a-zA-Z0-9=/+]{4})+)\n)+)'
    patternContentTypePlain = 'Content-Type: text/plain'
    patternContentTypeHtml = 'Content-Type: text/html'
    patternTransferEncoding = 'Content-Transfer-Encoding: '
    pattern_encoding_types = '(?P<Encoding>base64|quoted-printable)\n'
    patternQuoted = \
        '\n\n(?P<Content>([a-zA-Z0-9>?@\[\]^_`{|}~!"#$%&\'()*+,\-./:;<]|\S)*)'

    def __init__(self, message):
        """Constructor. Used to create an object from EmailMessage instance.

        Key arguments:
        message -- EmailMessage object used as underlying object.
        """
        self.email_message = message
        self.payload_list = []
        self._extract_meta_headers()

    def extract_payload(self):
        """ Extract payload/content parts from an email.

        Extract all content parts from the mail and create several payload
        objects form the extracted data.
        """
        matches = []
        # check if the message is multipart and perform the respective payload
        # pattern matching.
        if self.email_message.get_content_maintype() == 'multipart':
            pattern_list = [
                '(' + self.patternContentTypePlain + ').*\n'
                    + '\s*charset=\"(?:[a-zA-Z0-9_-]+)\"\n'
                    + self.patternTransferEncoding
                    + self.pattern_encoding_types
                    + '(?:.+\n)*'
                    + self.patternBase64,
                '(' + self.patternContentTypeHtml + ').*\n'
                    + '\s*charset=\"(?:[a-zA-Z0-9-_]+)\"\s*'
                    + self.patternTransferEncoding
                    + self.pattern_encoding_types
                    + '(?:.*:.*\n)*' + self.patternBase64,
                '(' + self.patternContentTypeHtml + ').*\s'
                    + '(?:\s*[-.;\w"]+=[-.;\w"]+\s*)*'
                    + self.patternTransferEncoding
                    + self.pattern_encoding_types
                    + '\s*' + self.patternHtml
            ]
            # check for all supported forms of payload int the whole mail
            matches = self._match_pattern_list(pattern_list)
            for match_obj in matches:
                transfer_encoding = self._retrieve_encoding(match_obj)
                content_type = self._retrieve_content_type(match_obj)
                self.payload_list.append(
                    self._create_payload_from_match(match_obj, content_type,
                                                    transfer_encoding))
        # if the mail is not multipart, we have to use different regex because
        # headers can be inserted between encoding information and content.
        else:
            content_type = ContentType.UNDEFINED
            content_charset = ''
            serialized_email = self.email_message.as_bytes().decode('utf-8',
                                                                    'ignore')
            # first check if it's some kind of text content
            match self.email_message.get_content_type():
                case 'text/plain':
                    content_type = ContentType.PLAINTEXT
                case 'text/html':
                    content_type = ContentType.HTMLTEXT
                case _:
                    content_type = ContentType.UNDEFINED
                    return
            # get the transfer encoding
            encoding_re = re.compile(self.pattern_encoding_types)
            match_obj = encoding_re.search(serialized_email)
            content_encoding = self._retrieve_encoding(match_obj)
            # depending on the encoding and content type, the char set
            # information can be found in different patterns.
            match content_encoding:
                case Encoding.BASE64:
                    content_re = re.compile(self.patternBase64)
                    content_charset = re.compile(
                            '\s*charset=\"([a-zA-Z0-9_-]+)\"\n').search(
                                                        serialized_email)
                case Encoding.QUOTEDPRINTABLE:
                    content_re = re.compile(self.patternQuoted)
                    pattern = '\s*charset=\"([a-zA-Z0-9_-]+)\"\n'
                    if content_type == ContentType.HTMLTEXT:
                        pattern = 'charset=3D(?P<charset>[a-zA-Z20-9-_]+' +\
                                  '(=\n[a-zA-z0-9-_]*)?)'
                    content_charset = re.search(pattern, serialized_email)
                case _:
                    content_charset = re.search('charset=(.*)',
                                                'charset=utf-8')
                    content_re = re.compile(self.patternQuoted)
            content_match = content_re.search(serialized_email)
            content = content_match.group('Content')
            # define the start and end in the serialized email
            start = content_match.start()
            end = content_match.end()
            # create a payload object and store it in the member list.
            payload = Payload(start, end, content, content_type,
                              content_encoding)
            payload.set_charset(re.subn(r'=\n', '',
                                        content_charset.group(1))[0])
            self.payload_list.append(payload)

    def update_content(self):
        """ Overwrite parts of the mail with the current payloads.

        Use this object's list of payload objects to overwrite the respective
        parts of the original mail with the payload's content. More detailed,
        content's are replaced in place in the email's serialized string
        representation. After replacement this string is parsed again to create
        a new EmailMessage from it.
        """
        serialized_email = self.email_message.as_bytes().decode('utf-8',
                                                                'ignore')
        # sort list by payload.start, so that the can be replaced in place in
        # the string.
        # key must be callable -> call lambda which returns start
        self.payload_list.sort(key=lambda h: (Payload.start))
        # offset stores the delta of length if the content moved to the front
        # or to the back because of indifferences between the original
        # content's length and the length of the new one.
        offset = 0
        result = ''
        prev_end = 0
        for payload in self.payload_list:
            orig_start = payload.start
            orig_end = payload.end
            # Copy the mail from the end of the previous processed payload to
            # the start of the current payload,
            result += serialized_email[prev_end:orig_start]
            # append the payload to the string
            result += payload.content
            prev_end = orig_end
            orig_len = orig_end - orig_start
            # update offset and start/end values respective to length delta of
            # preceding payloads
            if (len(payload.content)) != orig_len:
                payload.start += offset
                offset = orig_len - len(payload.content)
                payload.end += offset
        # add the missing parts of the mail after processing the last payload.
        if len(serialized_email) > prev_end:
            result += serialized_email[prev_end:]
        parser = email.parser.Parser(policy=email.policy.default)
        # we might have now a completely different message, so we should do the
        # initializing process again to override data of the old message
        self.email_message = parser.parsestr(result)
        self._update_meta_headers()
        self._extract_meta_headers()
        self.payload_list = []
        self.extract_payload()

    def _update_meta_headers(self):
        """ Propagate header modification to underlying EmailMessage object.
        """
        message = self.email_message
        for key in self.header_dict.keys():
            if message.get(key):
                message.replace_header(key, self.header_dict[key])
        self.email_message = message

    def _extract_meta_headers(self):
        """ Extract some chosen headers form the EmailMessage object.
        """
        message = self.email_message
        for key in self.header_dict:
            self.header_dict[key] = message.get(key)

    def _match_pattern_list(self, pattern_list):
        """Find matches in the serialized email.

        Kay arguments:
        patter_list -- List of pattern strings to search in the mail.

        Returns:
        A list of match_objects. Returns an empty list if no matches were
        found.
        """
        result = []
        serialized_email = self.email_message.as_bytes().decode('utf-8',
                                                                'ignore')
        for pattern in pattern_list:
            regexp = re.compile(pattern)
            for match_obj in regexp.finditer(serialized_email):
                result.append(match_obj)
        return result

    def _create_payload_from_match(self, match_obj, content_type,
                                   transfer_encoding):
        """ Create a payload form a match_obj and additional information.

        Key arguments:
        match_obj -- re.match_obj to generate the payload from
        content_type -- ContentType of the payload.
        transfer_encoding -- TransferEndoding of the payload.

        Returns:
        The newly created Payload object.
        """
        # Extract start, end and content of from the match_obj
        start = match_obj.start(3)
        end = match_obj.end(3)
        content = match_obj.group(3)
        # create payload
        payload = Payload(start, end, content, content_type, transfer_encoding)
        if payload.content_type == ContentType.PLAINTEXT:
            # find the character set in the match, if search was successful,
            # add character set to the payload.
            pattern = 'charset=\"(?P<charset>[a-zA-Z0-9-_]+)\"'
        elif payload.content_type == ContentType.HTMLTEXT:
            pattern = \
                'charset=3D(?P<charset>[a-zA-Z0-9-_]+(=\n[a-zA-z0-9-_]*)?)'
        charset_match = re.search(pattern, match_obj.group(0))
        if charset_match:
            char_set = quopri.decodestring(charset_match.group('charset'))
            payload.set_charset(str(char_set, 'utf-8').strip())
        return payload

    def _retrieve_encoding(self, match_obj):
        """Extract transfer encoding information from an re.match_obj.

        Key arguments:
        match_obj -- re.match_obj to extract the encoding from.

        Returns: 
        Value of enum 'Encoding'.
        """
        if match_obj is None:
            return Encoding.UNDEFINED
        match match_obj.group('Encoding'):
            case 'base64':
                return Encoding.BASE64
            case 'quoted-printable':
                return Encoding.QUOTEDPRINTABLE
            case _:
                return Encoding.UNDEFINED

    def _retrieve_content_type(self, match_obj):
        """ Extract content type of a mails content from an re.match_obj

        Key arguments:
        match_obj -- re.match_obj to extract content type information from.

        Returns:
        Value of enum 'ContentType'.
        """
        if match_obj is None:
            return ContentType.UNDEFINED
        match match_obj.group(1):
            case self.patternContentTypePlain:
                return ContentType.PLAINTEXT
            case self.patternContentTypeHtml:
                return ContentType.HTMLTEXT
            case _:
                return ContentType.UNDEFINED

    def __str__(self):
        result = 'This is an ExtendedEmailMessage object. \n'
        for key in self.header_dict.keys():
            result += "{0}: {1}\n ".format(key, self.header_dict[key])
        result += 'It contains the following payloads:\n'
        for payload in self.payload_list:
            result += str(payload)
            result += '-----------------------------------------------------\n'
        return result


class MailAnonymizer:
    """ Implements anonymization functions applicable to ExtendedEmailMessage.

    This class implements functions to anonymize several parts of objects of
    type ExtendedEmailMessage. It furthermore manages a lookup table to replace
    some data with the same replacement. To use this features one only needs to
    replace the value of the member 'extended_mail' and call the respective
    anonymization function. While in default mode only names and address parts
    of the 'To' header are replace, one has the possibility to state domains of
    interest in a block list. Adding this list will extend the search and
    replacement of mail aliases containing domains from the list.
    """
    extended_mail = None
    global_replacement_buffer = {}
    block_list = ()
    key_list = list()
    key_dict = dict()

    def __init__(self, extended_mail=None, block_list=None):
        """ Construct an object of class MailAnonymizer.

        Key arguments:
        extended_mail -- object of type ExtendedEmailMessage on which
        """
        self.extended_mail = extended_mail
        self.block_list = block_list

    def anonymize(self):
        """ Performs different anonymization steps. Overwrites internal mail.

        Different anonymization steps are performed on the different parts of
        an email, stored in 'extended_mail' member. In the result, the stored
        email message will be overwritten with the result of the anonymization.
        """
        self.key_dict = {}
        mail_to = self.extended_mail.header_dict['To']
        if mail_to != self.extended_mail.header_dict['From']:
            self.key_dict.update(self._split_to_into_word_list(mail_to))
        self.key_dict.update(self._include_block_list())
        self.key_dict.update(self._find_phone_numbers())
        self._find_replacements(self.key_dict)
        # we want to replace in a greedy manner and because we don't want to
        # sort all keys every time we need them, we will store a copy of the
        # keys as a list
        self.key_list = list(self.key_dict)
        self.key_list.sort(key=lambda h: len(h), reverse=True)
        self._anonymize_payload()
        self._anonymize_mail_headers()
        self.extended_mail.update_content()
        self._anonymize_plain()

    def _include_block_list(self):
        """Create regex patterns from the domains given by the block list.

        For later identification purpose, the pattern will be labeled as
        'email'.

        Return:
        dict() storing the pattern as key and the 'type' of the key as value.
        """
        result = {}
        if self.block_list is None:
            return result

        # create a reeeealy large string of the mail to search for any item of
        # the block list
        search_target = self.extended_mail.email_message.as_bytes().decode(
                                'utf-8', 'ignore')
        for payload in self.extended_mail.payload_list:
            search_target += payload.to_utf8()

        # now search for any item which could match with the block list
        for item in self.block_list:
            regex = re.compile('[-a-zA-Z0-9_.]+@[-a-zA-Z0-9_.]*' +
                               re.escape(item))
            for hit in regex.findall(search_target):
                result[hit] = 'email'
                result.update(self._split_to_into_word_list(hit))
        return result

    def _find_phone_numbers(self):
        """ Extract phone numbers from all mail payloads.

        Phone numbers will be labeled as 'phone' for later identification
        purpose.

        Returns:
        dict() with phone number as key and label as value.
        """
        phone_regex = re.compile(r"""
            \+?         # optional + before country code
            \d{1,4}?    # country code
            [-.\s]?     # delimiter after after country code
            \(?         # optional opening bracket
            \d{1,3}?    # area code
            \)?         # optional closing bracket after area code
            [-.\s]?     # optional delimiter after area code
            \d{1,4}     # begin of phone number with optional delimiters
            [-.\s]?
            \d{1,4}
            [-.\s]?
            \d{2,9}
            """,
                                 re.X)
        result = dict()
        for payload in self.extended_mail.payload_list:
            # search only in text content
            if (payload.content_type == ContentType.PLAINTEXT) or \
               (payload.content_type == ContentType.HTMLTEXT):
                string = payload.to_utf8()
                numbers = phone_regex.findall(string)
                for number in numbers:
                    # assign label for later replacement
                    result[number] = 'phone'
        return result

    def _perform_replacement(self, target_string):
        """ Help function that performs replacement operation,

        This function performs the replacement operations according to the
        member variable 'self.key_list' on a given string.

        Key arguments:
        target_string --  string on which the replacement is performed.

        Returns:
        A string in which all keys from the dict were replaced.
        """
        result = target_string
        for key in self.key_list:
            replacement_target = key
            replacement = self.key_dict[key]
            replacement_target = re.escape(replacement_target)
            replacement_re = re.compile(replacement_target)
            result = replacement_re.subn(replacement, result)[0]
        return result

    def _anonymize_payload(self):
        """Anonymize all payloads of the locally stored email.

        Overwrite the content of all text payloads with their anonymized
        version. That means, strings which should be replaced, are replaced and
        the resulting string is then used to overwrite the content.
        """
        for payload in self.extended_mail.payload_list:
            if (payload.content_type == ContentType.PLAINTEXT) or \
               (payload.content_type == ContentType.HTMLTEXT):
                string = payload.to_utf8()
                string = self._perform_replacement(string)
                payload.set_text_content(string)

    def _anonymize_mail_headers(self):
        """Anonymize a given set of headers.

        Headers which should be replaced are specified in the class
        'ExtendedEmailMessage' in 'header_dict'. Values of headers will be
        overwritten by their respective replacement.
        """
        for header in self.extended_mail.header_dict.keys():
            header_value = self.extended_mail.header_dict[header]
            if header_value is None:
                continue
            header_value = self._perform_replacement(header_value)
            self.extended_mail.header_dict[header] = header_value

    def _anonymize_plain(self):
        """ Perform anonymization on the mails raw data.

        In some cases data worth protecting is located in the raw mail data,
        e.g. in a header not noted by the other replacement routines. This
        function aims to replace such data in the raw mail data.
        After replacing all found data, the resulting raw mail string is used
        to create a new EmailMessage object, by parsing the string.
        """
        mail_string = self.extended_mail.email_message.as_bytes().decode(
                                'utf-8', 'ignore')
        mail_string = self._perform_replacement(mail_string)
        parser = email.parser.Parser(policy=email.policy.default)
        self.extended_mail.email_message = parser.parsestr(mail_string)

    def _find_replacements(self, replacement_candidates):
        """Creates random replacements for each dict key.

        For each key value in replacement_candidates, are random replacement is
        generated using the python library called faker. The label, stored as
        value of each item in replacement_candidates, is used to make faker
        generate a fitting replacement. In the result, the label will be
        overwritten with the respective replacement.

        Key arguments:
        replacement_candidates -- Dict containing the value which should be
                                  replaces as key and it's label as value
        """
        fake = Faker()
        new_values = {}
        for to_replace in replacement_candidates:
            match replacement_candidates[to_replace]:
                case 'name':
                    # names can occur in different form in a mail. To aide this
                    # fact, we generate different versions of each name.
                    fake_name = fake.first_name()
                    new_values[to_replace] = fake_name
                    new_values[to_replace.capitalize()] = fake_name
                    new_values[to_replace.lower()] = fake_name
                    new_values[to_replace.upper()] = fake_name
                case 'email':
                    new_values[to_replace] = fake.ascii_safe_email()
                case 'phone':
                    new_values[to_replace] = fake.phone_number()
            # names are irrelevant when viewing spam campaigns. All other data
            # is more or less relevant when clustering spam. Therefore we need
            # to store replacement pairs in a dict used for all mails in later
            # runs.
            if 'name' != replacement_candidates[to_replace]:
                if to_replace not in self.global_replacement_buffer.keys():
                    self.global_replacement_buffer.update(new_values)
            if to_replace in self.global_replacement_buffer.keys():
                new_values[to_replace] = self.global_replacement_buffer[
                                                                    to_replace]
        # override each label by the respective replacement.
        replacement_candidates.update(new_values)

    def _split_to_into_word_list(self, from_string):
        """The given string is split into pieces.

        Email addresses can consist of a concatenation of different names, each
        one representing data which should be protected. This function splits
        strings which contain names and/or mail addresses into part. Splitting
        for email addresses is performed at the characters [-@._]. The results
        of the splitting are labeled accordingly.

        Key arguments:
        from_string --  string to split into different parts.

        Returns:
        Dict containing the part of the original string as key and their
        respective label as value.
        """
        result = dict()
        if from_string is None:
            return result

        # first convert to lower case
        string = from_string
        # Use the following regex to find name and/or email address of the
        # recipient. The regex recognises one of the following three patterns:
        #   form of header | pattern
        #   ---------------+-----------------------
        #   name only      | "surname, forename "
        #   email only     | <mail.address@domain.second.example>
        #   email and name | "forename surname" <mail@domain.example>
        #
        # Mail addresses can contain an unspecified number of subdomains. Names
        # must consist of at least two words. Both can contain alphanumeric
        # characters. If the name part matches, a group with id 'name' will be
        # returned by the match object. Analog with the email pattern, of which
        # the id is 'email'.
        regexp = re.compile(r"""
            (?:"?
                (?P<name>              # assign group name 'name'
                    [\w\-]+,?(?:\s[\w\-]+)+    # match fore-and last name
                )                      # can be comma separated
            "?)?                       # omit if only mail is to be matched
            \s?                        # space between mail address and name
            (?:<?
                (?P<email>             # assign group name 'email'
                    [_\w\-]+(\.?[_\w\-]+)*@[_\w\-]+(\.[-_\w]+)+  # match email
                )
             >?)?                      # omit if only name is to be matched
            """, re.X)
        match_result = regexp.search(string)

        # create a list of potential words which should be replaced
        match_group_keys = ['name', 'email']
        for key in match_group_keys:
            group_result = match_result.groupdict()[key]
            if group_result:
                if key == 'name':
                    for word in group_result.split():
                        result[word.rstrip(',')] = key
                elif key == 'email':
                    result[group_result.split('@')[0]] = 'name'
                    for name in group_result.split('@')[0].split('.'):
                        result[name] = 'name'
                    result[group_result] = key
        return result


def main():
    argv = sys.argv
    argc = len(sys.argv)
    if argc > 0:
        print('This script was started as main for debugging purposes.')
        print('Using "', argv[1], '"as input.')
        fn = argv[1]
        file_list = list()
        if os.path.isdir(fn):
            print('Input is directory...')
            file_list = filter(lambda i: (os.path.splitext(i)[1] == '.eml'),
                               os.listdir(fn))
            file_list = [os.path.join(fn, file) for file in file_list]
        else:
            file_list = [fn]
        block_list = list()
        if len(argv) > 2:
            out_path = argv[2]
            if os.path.isdir(out_path):
                print('Writing output to', out_path)
            else:
                create = input(out_path + ' does not exist. Create? [y|n]')
                if create == 'y':
                    os.mkdir(out_path)

        if len(argv) > 3:
            print("Reading block list from...", argv[3])
            with open(argv[3], 'r') as block_file:
                line = block_file.readline()
                while line:
                    line = line.strip()
                    block_list.append(line)
                    line = block_file.readline()
        anonymizer = MailAnonymizer(None, block_list)
        list_len = len(file_list)
        count = 1
        error_log = list()
        for file in file_list:
            print('[{0}|{1}] Processing {2}'.format(count, list_len, file))
            try:
                message = mailIo.readMailFromEmlFile(file)
                extMessage = ExtentedEmailMessage(message)
                extMessage.extract_payload()
                anonymizer.extended_mail = extMessage
                anonymizer.anonymize()
                out_file = os.path.join(out_path, os.path.split(file)[1])
                mailIo.writeMessageToEml(extMessage.email_message, out_file)
            except UnicodeEncodeError as u_error:
                error_string = \
                    'Mail {} is ill formed and therefore skipped!'.format(file)
                error_log += error_string + str(u_error) + '\n'
                print(error_string)
            except ValueError as v_error:
                error_string = \
                    'Mail {} produced a ValueError:{}'.format(file,
                                                              str(v_error))
                error_log += error_string + '\n'
                error_log += "Content of mail:\n"
                error_log += str(extMessage.header_dict) + '\n'
                print(error_string)
            count += 1
            log_path = os.path.join(out_path, 'error_log.txt')
        with open(log_path, 'w') as log_file:
            log_file.writelines(error_log)
    else:
        print("Path was not given")


if __name__ == "__main__":
    main()
