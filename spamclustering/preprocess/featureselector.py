import os.path
import re

import spamclustering.preprocess.payload as pl
import spamclustering.preprocess.htmlskeletonparser as hs

class FeatureSelector:
    """ Performs feature selection on ExtendedEmailMessage objects.

    This Helper class collects and manages features collected from 
    objects of type :class:
    `spamclustering.preprocess.extendedemailmessage.ExtededEmailMessage`.
        
    Upon creation this FeatureSelector will begin to extract features from
    ExtendedEmailMessage objects. For each message a dict of features is 
    created. Each dict is stored in a memeber called feature list. An 
    additional member dict, called feature_avaiability, stores which 
    features should be processed later. The only affect this has on this 
    class is, that the __str__ method will only consider features marked as 
    True when creating the string representation. 

    :param feature_list: List containing the feature representation of 
      `spamclustering.preprocess.extendedemailmessage.ExtededEmailMessage`
       objects.
       Available Features (keys) are as of now:
       * 'serialized_string': String representation of a message, e.g. as 
             read from eml file.
       * 'text_payloads': A list of all payload parts of the mail containing
             only text.
       * 'html_payloads': A List of all payload parts of the mail contaiing
             HTML text.
       * 'image_payloads': A list of all payload parts of the mail
             consisting of images.
       * 'payload_types': A list of payload types of the mail.
       * 'subject': The subject of the mail as UTF-8 string.
       * 'html_skeletons': A list of HTML skeletons of all HTML payloads of 
             the mail. A skeleton is all HTML tags of the mail without any 
              content.
       * 'uri_amount' : total count of found URIs in the mail (all content 
             parts)
       * 'schemes_string' : String resulting form concatenating all scheses 
             cointained in the found found URIs
       * 'hosts_string' : String creating from concatenating all host parts of 
             URIs found in all content parts.
       * 'total_attachment_size': Size in KiBytes as String, obtained from 
             suming up the size of all attachments.
       * 'attachment_fil_extensions': String created from concatenating the 
             file extension foudn from all attachments.
       * 'attachment_names': String created from concatenating all extension 
             file names.
    
    :type feature_dict: dict of dicts with mentioned keys.
    :param feature_availability: Helper dict storing what feature should be
        made available to other objects.
    :type feature_availability: dict(), string as keys, Boolean as value
    """
    def __init__(self, list_of_messages):
        """ Constructor
        :param list_of_messages: A list of messages from which feature should 
            be extracted
        :type list_of_messages: list of 
          `spamclustering.preprocess.extendedemailmessage.ExtededEmailMessage`
        """
        self.feature_dict = dict()
        self.feature_availability = {
            'serialized_string': True,
            'text_payloads': True,
            'html_payloads': True,
            'image_payloads': True,
            'payload_types': True,
            'subject': True,
            'html_skeletons': True
        }
        # process messages
        for message in list_of_messages:
            feature_dict = self._collect_features(message)
            self.feature_dict[message.id] = feature_dict

    def _collect_features(self, message):
        """ Helper function to collect all features.
        Calls other helper functions.
        """
        feature_dict = dict()
        #feature_dict['serialized_string'] = message.email_message.as_string()
        feature_dict['subject'] = message.email_message.get('subject', '')
        # add payloads by type to feature list
        feature_dict.update(self._process_payloads(message))
        feature_dict.update(self._search_for_uris(message))
        feature_dict.update(self._process_attachments(message))
        return feature_dict

    def _process_payloads(self, message):
        """ Extarcts features from payloads.
        """
        available_types = ''
        feature_dict = dict()
        feature_dict['text_payloads'] = ''
        feature_dict['html_payloads'] = ''
        feature_dict['image_payloads'] = ''
        feature_dict['payload_types'] = ''
        feature_dict['html_skeletons'] = ''
        for payload in message.payload_list:
            match(payload.content_type):
                case pl.ContentType.PLAINTEXT:
                    feature_dict['text_payloads'] += payload.to_utf8()
                    available_types += 'text'
                case pl.ContentType.HTMLTEXT:
                    utf8_payload = payload.to_utf8()
                    feature_dict['html_payloads'] += utf8_payload
                    available_types += 'html'
                    feature_dict['html_skeletons'] += \
                        self._extract_html_skeleton(utf8_payload)
                case pl.ContentType.IMAGE:
                    feature_dict['image_payloads'] += payload.content
                    available_types += 'image'
        feature_dict['payload_types'] = available_types
        return feature_dict

    def _extract_html_skeleton(self, html_string):
        """ Helper function to extarct HTML skeleton.
        """
        result = ''
        skeleton_parser = hs.HTMLSkeletonParser()
        skeleton_parser.feed(html_string)
        result = skeleton_parser.close()
        return result

    def _search_for_uris(self, message):
        uri_re = re.compile(r"""(
                            # first common URI schemes used for web content
                            # btw make all inner regexs uncapturing
                            (?P<scheme>https|http|ftp|mailto|file|data|irc):
                            # now match any characte which is not whitespace
                            (?:// # begin fo authority
                                (?P<user>
                                    # user info
                                    [a-zA-Z0-9\-_\.~/\[\]]+
                                    @
                                )?
                                # host
                                (?P<host>
                                    [a-zA-Z0-9\-_\.~/\[\]]+
                                    (?:
                                        #port
                                        :[0-9]+
                                    )?
                                )?
                            )?
                            # path 
                            (?P<path>[a-zA-Z0-9\-_\.~/\[\]]+)
                            (?P<query>
                                # query
                                \?[a-zA-Z0-9\-_\.~/\[\]]+
                            )?
                            (?P<fragment>
                                #fragment
                                \#[a-zA-Z0-9\-_\.~/\[\]]+
                            )?
                            )
                            """, re.X)
        uri_list = []
        for payload in message.payload_list:
            # will return None, if no plain text/html text
            payload_utf8 = payload.to_utf8() 
            if payload_utf8:
                for uri in uri_re.finditer(payload_utf8):
                    if uri not in uri_list:
                        uri_list.append(uri)
        list_of_schemes = []
        list_of_hosts = []
        list_of_paths = []
        list_of_fragments = []
        for uri in uri_list:
            scheme = str(uri.group('scheme'))
            host = str(uri.group('host'))
            if scheme not in list_of_schemes:
                list_of_schemes.append(scheme)
            if host not in list_of_hosts:
                list_of_hosts.append(host)

        schemes_as_string = ''
        for scheme in sorted(list_of_schemes):
            schemes_as_string += scheme
        
        hosts_as_string = ''
        for host in sorted(list_of_hosts):
            hosts_as_string += host

        features = {
            'uri_amount' : str(len(uri_list)),
            'schemes_string' : schemes_as_string,
            'hosts_string' : hosts_as_string
        }

        return features

    def _process_attachments(self, message):
        size_as_string = ''
        
        list_of_names = []
        total_size = 0
        list_of_types = []
        for attachment in message.email_message.iter_attachments():
            name_match = re.search(r'name="(?P<file_name>.*)"', 
                                   attachment.get('Content-Type', ''))
            if name_match:
                attachment_name = name_match.group('file_name')
                list_of_names.append(attachment_name)
                ext = os.path.splitext(attachment_name)[1]
                if ext not in list_of_types:
                    list_of_types.append(ext)
            # content lenght is lenght in bytes of the encoded content
            total_size += len(attachment.as_bytes())

        names_of_attachments = ''
        for name in sorted(list_of_names):
            names_of_attachments += name

        file_extensions = ''
        for extension in sorted(list_of_types):
            file_extensions += extension

        # an uncompressed image of size 128x128 with 32 bit color space has a 
        # size of 64 KiByte. So iterating in 64KiB steps seems good?
        step_size = 64 * 1024
        max_size = 256*step_size
        size_string = str(max_size)
        # maybe the increment must be higher
        for size in range(step_size, max_size, step_size):
            if total_size < size:
                size_string = str(size)
                break

        result = {
            'total_attachment_size': size_string,
            'attachment_fil_extensions': file_extensions,
            'attachment_names': names_of_attachments
        }
        return result

    def toggle_feature(self, feature):
        """ Toggle feature availability.
        Features which are available will be unavailable after toggling and 
        vice versa.
        :param feature: String of the feature to toggle availability of.
        :type feature: string
        :return: The new availability of the gieven feature. False if not 
            available and True, if available.
        :rtype: Boolean 
        """
        new_value = not self.feature_availability[feature]
        self.feature_availability[feature] = new_value
        return new_value

    def get_categorigal_features(self):
        """ Returns a feature dict containing only categorigal features.
        """

        categorigal_keys = [
            'payload_types',
            'uri_amount',
            'schemes_string',
            'hosts_string',
            'total_attachment_size',
            'attachment_fil_extensions'
        ]
        return self.collect_features_from_keys(categorigal_keys)

    def get_non_categorigal_features(self):
        """ Returns a feature dict containing only categorigal features.
        """
        non_categorical_keys = [
            'text_payloads',
            'html_payloads',
            'image_payloads',
            'payload_types',
            'subject',
            'html_skeletons',
            'attachment_names'
        ]
        return self.collect_features_from_keys(non_categorical_keys)
    
    def collect_features_from_keys(self, key_list):
        result = dict()
        for mail_id, feature_vector in self.feature_dict.items():
            result[mail_id] = dict()
            for key in key_list:
                result[mail_id].update({key : feature_vector[key]}) 
        return result

    def __str__(self):
        """ Create string representation.
        """
        result = ''
        for _, feature_dict in self.feature_dict.items():
            for key, item in feature_dict.items():
                if self.feature_availability[key] == True:
                    result += str(key) + ': ' + str(item) + '\n'
            result += '-------------------------------------'
        return result
