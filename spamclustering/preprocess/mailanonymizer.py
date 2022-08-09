import re
import email

from faker import Faker

import spamclustering.preprocess.payload as pl


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
    global_replacement_buffer = {}
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
            if (payload.content_type == pl.ContentType.PLAINTEXT) or \
               (payload.content_type == pl.ContentType.HTMLTEXT):
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
            if (payload.content_type == pl.ContentType.PLAINTEXT) or \
               (payload.content_type == pl.ContentType.HTMLTEXT):
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
