import re
import quopri
import email

import spamclustering.preprocess.payload as pl


class ExtentedEmailMessage:
    """ Adds additional modification functions to python EmailMessage.

    This class add a more complex payload/content part detection to python
    EmailMessage class.

    :param message: Email message to build this object around.
    :type message: :class:`email.message.Message`
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
    """Dict of knwon headers to process."""
    # some pattern strings to create regular expressions from
    # Because of bad design decisions the html pattern contains a pattern for
    # quoted printable encoded and plain text. TODO: rework all regular
    # expression to split the task of searching for payload and header data
    patternHtml = '(?P<Content>(<html(?:.|\s)*/html>)|' + \
                  '(<=?\s?h=?\s?t=?\s?m=?\s?l=?\s?>(?:.\s)*' + \
                  '/=?\s?h=?\s?t=?\s?m=?\s?l=?\s?>))'
    """Regex pattern for detecting html content"""
    patternBase64 = '\n(?:(?:(?:[a-zA-Z0-9=/+]{4})+)\n)+'

    patternContentType = 'Content-Type: (?P<ContentType>[a-z]+/\w+)'
    """Regex pattern for detecting 'text/html' content type."""
    patternTransferEncoding = 'Content-Transfer-Encoding: ' + \
                              '(?P<Encoding>base64|quoted-printable)\n'
    """Regex pattern for detecting transferencoding type"""
    patternQuoted = \
        '\n' + \
        '((([a-zA-Z0-9>?@\[\]^_`{|}~!"#$%&\'()*+,\-./:;<\s\\\])|' + \
        '(=[0-9A-F][0-9A-F]))+=?\n)*'
    """Regex pattern for detecting quoeted printable content."""

    def __init__(self, message, id):
        self.id = id
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
                 self.patternContentType + '.*\s'
                 + '(?:\s*[-.;\w"]+=[-.;\w"]+\s*)*'
                 + self.patternTransferEncoding
                 + '(?:Content-ID: (?P<ContentID>.*)\n)?'
                 + '\s*' + '(?P<Content>' + self.patternBase64 + '|' +
                 self.patternQuoted + ')'
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
            content_type = pl.ContentType.UNDEFINED
            content_charset = ''
            serialized_email = self.email_message.as_bytes().decode('utf-8',
                                                                    'ignore')
            # first check if it's some kind of text content
            match self.email_message.get_content_type():
                case 'text/plain':
                    content_type = pl.ContentType.PLAINTEXT
                case 'text/html':
                    content_type = pl.ContentType.HTMLTEXT
                case _:
                    content_type = pl.ContentType.UNDEFINED
                    return
            # get the transfer encoding
            encoding_re = re.compile(self.patternTransferEncoding)
            match_obj = encoding_re.search(serialized_email)
            content_encoding = self._retrieve_encoding(match_obj)
            # depending on the encoding and content type, the char set
            # information can be found in different patterns.
            match content_encoding:
                case pl.Encoding.BASE64:
                    content_re = self.patternBase64
                    content_charset = re.compile(
                            '\s*charset=\"([a-zA-Z0-9_-]+)\"\n').search(
                                                        serialized_email)
                case pl.Encoding.QUOTEDPRINTABLE:
                    content_re = '\n' + self.patternQuoted
                    pattern = '\s*charset=\"([a-zA-Z0-9_-]+)\"\n'
                    if content_type == pl.ContentType.HTMLTEXT:
                        pattern = 'charset=3D(?P<charset>[a-zA-Z20-9-_]+' +\
                                  '(=\n[a-zA-z0-9-_]*)?)'
                    content_charset = re.search(pattern, serialized_email)
                case _:
                    content_charset = re.search('charset=(.*)',
                                                'charset=utf-8')
                    content_re = self.patternQuoted
            content_re = re.compile('(?P<Content>' + content_re + ')')
            content_match = content_re.search(serialized_email)
            content = content_match.group('Content')
            # define the start and end in the serialized email
            start = content_match.start()
            end = content_match.end()
            # create a payload object and store it in the member list.
            payload = pl.Payload(start, end, content, content_type,
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
        self.payload_list.sort(key=lambda h: (h.start))
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
            # preceding payloads:
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

        :param pattern_list: List of pattern strings to search in the mail.
        :type pattern_list: list of str

        :return: A list of match_objects. Returns an empty list if no matches
            were found.
        :rtype: list of :class:`re.Match`
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

        :param match_obj: match  to generate the payload from
        :type match_obj: :class:`re.Match`
        :param content_type: ContentType of the payload.
        :type content_type:
            :class:`spamclustering.preprocess.encodingConverter.ContentType`
        :param transfer_encoding: TransferEndoding of the payload.
        :type transfer_encoding:
            :class:`spamclustering.preprocess.encodingConverter.Encoding`
        :returns: The newly created Payload object.
        :rtype:
            :class:`spamclustering.preprocess.encodingConverter.Payload`
        """
        # Extract start, end and content of from the match_obj
        start = match_obj.start('Content')
        end = match_obj.end('Content')
        content = match_obj.group('Content')
        # create payload
        payload = pl.Payload(start, end, content,
                             content_type[0], transfer_encoding)
        payload.extension = content_type[1]
        is_text = payload.content_type in [pl.ContentType.PLAINTEXT,
                                           pl.ContentType.HTMLTEXT]
        # if we got some kind of text payload, we might want to extract the
        # text's character set information for corrent en- and decoding.
        if is_text is True:
            if (payload.encoding_type is pl.Encoding.QUOTEDPRINTABLE) and \
               (payload.content_type is pl.ContentType.HTMLTEXT):
                pattern = \
                    'charset=3D(?P<charset>[a-zA-Z0-9-_]+(=\n[a-zA-z0-9-_]*)?)'
            else:
                pattern = 'charset=\"(?P<charset>[a-zA-Z0-9-_]+)\"'
            charset_match = re.search(pattern, match_obj.group(0))
            if charset_match:
                char_set = quopri.decodestring(charset_match.group('charset'))
                payload.set_charset(str(char_set, 'utf-8').strip())
        return payload

    def _retrieve_encoding(self, match_obj):
        """Extract transfer encoding information from an re.match_obj.

        :param match_obj: Match to extract the encoding from.
        :type match_obj: :class:`re.Match`
        :returns: Transfer encoding type.
        :rtype:
            :class:`spamclustering.preprocess.encodingConverter.Encoding`
        """
        if match_obj is None:
            return pl.Encoding.UNDEFINED
        match match_obj.group('Encoding'):
            case 'base64':
                return pl.Encoding.BASE64
            case 'quoted-printable':
                return pl.Encoding.QUOTEDPRINTABLE
            case _:
                return pl.Encoding.UNDEFINED

    def _retrieve_content_type(self, match_obj):
        """ Extract content type of a mails content from an re.match_obj

        :param match_obj: Match to extract content type information from.
        :type match_obj: :class:`re.Match`

        :returns: Type of the paylaod.
        :rtype:
            :class:`spamclustering.preprocess.encodingConverter.ContentType`
        """
        if match_obj is None:
            return pl.ContentType.UNDEFINED
        content_extension = match_obj.group('ContentType').split('/')
        content_type = content_extension[0]
        extension = content_extension[1]
        match (content_type, extension):
            case ('text', 'plain'):
                return (pl.ContentType.PLAINTEXT, extension)
            case ('text', 'html'):
                return (pl.ContentType.HTMLTEXT, extension)
            case ('image', _):
                return (pl.ContentType.IMAGE, extension)
            case _:
                return pl.ContentType.UNDEFINED

    def __str__(self):
        result = 'This is an ExtendedEmailMessage object. \n'
        for key in self.header_dict.keys():
            result += "{0}: {1}\n ".format(key, self.header_dict[key])
        result += 'It contains the following payloads:\n'
        for payload in self.payload_list:
            result += str(payload)
            result += '-----------------------------------------------------\n'
        return result
