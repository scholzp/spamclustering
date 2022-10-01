class ClusteringProfiler:
    """ Small helper class for profiling sets of clusters.

    currently accessible member values:
    cluster_member_count: Total number of all members of clusters.
    cluster_count: Total number of all clusters in the given set.
    member_duplicates: Dictonary with all cluster members contained in muttiple 
                       clusters.
    avg_cluster_size: Average cluster size. Calculate by cluster_member_count 
                      by cluster_count.

    :param set_of_clusters: set of clusters to evaluate.
    :type input_list: set of 
        :class:
            `spamclustering.algorithms.spamclustering.spamcluster.SpamCluster`
    """

    def __init__(self, set_of_clusters):
        self.set_of_clusters = set_of_clusters
        # iterate over all clusters once for profiling
        total_cluster_num = 0
        total_file_num = 0
        member_dict = {}
        for cluster in set_of_clusters:
            for member_id,_ in cluster.invert().items():
                if member_id in member_dict.keys():
                    member_dict[member_id].append(cluster.uuid)
                else: 
                    member_dict[member_id] = [cluster.uuid]
        self.cluster_member_count = len(member_dict.keys())
        self.cluster_count = len(set_of_clusters)
        self.member_duplicates = dict((mb, cl) for mb, cl 
                                       in member_dict.items() if len(cl) > 1)
        self.avg_cluster_size = self.cluster_member_count / self.cluster_count

    def __str__(self):
        result = 'Absolut number of cluster members: '
        result += str(self.cluster_member_count) + '\n'
        result += 'Absolut number of clusters: '
        result += str(self.cluster_count) + '\n'
        result += 'Avg. cluster size: ' + str(self.avg_cluster_size) + '\n'
        result += 'Members contained in more than one cluster (duplicates):\n'
        for duplicate, clusters in self.member_duplicates.items():
            result += str(duplicate) + ' : ' + str(clusters) + '\n'
        return result