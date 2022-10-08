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
       * 'id' : The Id of the message to which the feature dict belongs
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
        feature_dict['serialized_string'] = message.email_message.as_string()
        feature_dict['subject'] = message.email_message.get('subject', '')
        # add payloads by type to feature list
        feature_dict.update(self._process_payloads(message))

        return feature_dict

    def _process_payloads(self, message):
        """ Extarcts features from payloads.
        """
        available_types = []
        feature_dict = dict()
        feature_dict['text_payloads'] = []
        feature_dict['html_payloads'] = []
        feature_dict['image_payloads'] = []
        feature_dict['payload_types'] = []
        feature_dict['html_skeletons'] = []
        for payload in message.payload_list:
            match(payload.content_type):
                case pl.ContentType.PLAINTEXT:
                    feature_dict['text_payloads'].append(payload.to_utf8())
                    available_types.append('text')
                case pl.ContentType.HTMLTEXT:
                    utf8_payload = payload.to_utf8()
                    feature_dict['html_payloads'].append(utf8_payload)
                    available_types.append('html')
                    feature_dict['html_skeletons'].append(
                        self._extract_html_skeleton(utf8_payload))
                case pl.ContentType.IMAGE:
                    feature_dict['image_payloads'].append(payload.content)
                    available_types.append('image')
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
