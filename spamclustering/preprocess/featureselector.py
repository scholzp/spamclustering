class FeatureSelector:
    def __init__(self, list_of_messages):
        self.feature_list = []
        for message in list_of_messages:
            feature_dict = self._collect_features(message)
            self.feature_list.append(feature_dict)

    def _collect_features(self, message):
        feature_dict = dict()
        feature_dict['id'] = message.id
        feature_dict['serialized_string'] = message.email_message.as_string()

        return feature_dict

