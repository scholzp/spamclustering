import ssdeep

from .clusteringalgorithm import ClusteringAlgorithm
from .spamcluster import SpamCluster


class Ctph(ClusteringAlgorithm):
    """ Implements context triggered piecewise hash algorithm.

    The actual hashing and compare algorithms are provided by the library
    ssdeep, developed by Jesse Kornblum. This c library is used with python
    bindings which can be installed pypi ssdeep package. If the similarity
    score of two hash values are greater than a threshold value, they will
    potentially grouped in one cluster. An email is only added to the cluster
    containing the mail with the greatest similarity score.

    :param input_list: List of file names to process.
    :type input_list: str or list of str
    :param output_path: Path to the location to which all cluster should be
        written to.
    :type output_path: str
    :param threshold_value: Threshold of matching score. If matching score is
        greater, the files are considered a match.
    :type threshold_value: int or float
    """

    def __init__(self, feature_dict, output_path, threshold=80):
        ClusteringAlgorithm.__init__(self, feature_dict, output_path)
        self.threshold_value = threshold

    def do_clustering(self):
        """Concrete implementation specific to the algorithm.

        For further details on the algorithm, read the class doc string.
        """
        # dict to store hash values of each file
        hash_dict = {}
        # calculate hash value for each file
        for mail_id, feature_vector in self.feature_dict.items():
            # concat all features to one string containing the whole feature 
            # vector so one can calculate a hash from it
            feature_string = ''
            for _, feature_value in feature_vector.items():
                feature_string += feature_value
            hash_dict[mail_id] = ssdeep.hash(feature_string)

        # use a dict to store which file belongs to which cluster
        file_cluster_dict = {}
        # perform the clustering, comparing each file to all others
        for current in hash_dict.keys():
            # we need to somehow store the best matching email. Therefore we
            # safe the filename together with the matching score.
            best_match = ('', 0)
            for comp in hash_dict.keys():
                if current != comp:
                    # calculate matching score
                    match_degree = ssdeep.compare(hash_dict[current],
                                                  hash_dict[comp])
                    # check if score exceeds threshold and if the score is
                    # greater than the current best match
                    if (match_degree > self.threshold_value) and \
                       (match_degree > best_match[1]):
                        best_match = (comp, match_degree)

            cluster = None
            # add the current file either to an existing cluster (that with the
            # best match) or create a new one.
            if best_match[0] in file_cluster_dict.keys():
                cluster = file_cluster_dict[best_match[0]]
                cluster.add(current)
            else:
                cluster = SpamCluster()
                cluster.add(current)
                self.cluster_dict[cluster.uuid] = cluster
            file_cluster_dict[current] = cluster
