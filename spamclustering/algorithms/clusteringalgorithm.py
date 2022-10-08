import spamclustering.algorithms.spamcluster as sc


class ClusteringAlgorithm:
    """Base class for clustering algorithms.

    Implements some boiler plate code for writing clusters to disk.
    """
    def __init__(self, feature_dict, output_path):
        """ Constructor which should be used for this class.
        Providing the required arguments will result in a ready to use
        algorithm, which can do the clustering and is able to write the results
        back to disk.

        :param input_dict: dict of mail IDs and their respective feature.
        :type input_dict: dict 
        :param output_path: Path to the location to which all clusters should
            be written to.
        :type output_path: str
        """
        self.feature_dict = feature_dict
        self.output_path = output_path
        self.input_path = ''
        self.cluster_dict = {}

    def do_clustering(self):
        """ Performs the class specific clustering algorithm.

        The base class creates one cluster and adds all items to this cluster.
        This function is to be overwritten by classes which inherited from
        ClusteringAlgorithm and implement own clustering algorithms.
        """
        new_cluster = sc.SpamCluster()
        input_files = [mail_id 
                        for mail_id, features in self.feature_dict.items()]
        new_cluster.add(self.input_files)
        self.cluster_dict[new_cluster.uuid] = new_cluster

    def write_cluster_to_disk(self):
        """ Writes all clusters in cluster_dict to disk.

        Path is specified through self.output_path, which was set when calling
        the respective constructor. Needs to be set otherwise.
        """
        for _, cluster in self.cluster_dict.items():
            cluster.write_to_path(self.output_path)
