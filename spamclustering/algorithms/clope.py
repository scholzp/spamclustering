import math
import copy

from scipy import stats as sps
from .clusteringalgorithm import ClusteringAlgorithm
from .spamcluster import SpamCluster


class ClopeCluster(SpamCluster):
    """ Extends SpamCluster.

    A cluster needs to offer some more functionality when using it for 
    clustering with the clope algorithm. 
    """
    def __init__(self):
        SpamCluster.__init__(self)
        self.item_frequency = dict()
    

    def add(self, file_id, feature_vector):
        """ Add file to cluster. Process feature vector of file.

        Additional feature_vector paramater is processed to enable the class 
        to later calculate important values. feature_vector is processed in a 
        way that the so called item frequency, the frequency of a feature 
        value, in this cluster can be calculated.

        :param file_id: File name or id
        :type file_id: str
        :param feature_vector: feature vector of the file with file id file_id
        :type feature_vector: dict of features and their respective values.
        """
        SpamCluster.add(self, file_id)
        for feature, value in feature_vector.items():
            if feature in self.item_frequency.keys():
                self.item_frequency[feature] += 1
            else:
                self.item_frequency[feature] = 1

    def remove(self, file_id, feature_vector):
        """ Removes a feature vector from cluster.
        """
        remove_list = []
        for feature, value in feature_vector.items():
            if feature in self.item_frequency.keys():
                self.item_frequency[feature] -= 1
                if self.item_frequency[feature] < 1:
                    remove_list.append(feature)
        for feature in remove_list:
            if feature in self.item_frequency.keys():
                del self.item_frequency[feature]
        self.cluster_members.remove(file_id)

    def num_of_members(self):
        """ Returns number of members.

        :return: Number of members.
        :rtype: int 
        """
        return len(self.cluster_members)

    def num_of_items(self):
        """ Returns number of items.

        An item is a value of a feature vector. The number of all items is 
        summed up and returned.

        :return: Number of items
        :rtype: int
        """ 
        result = 0
        for item, frequency in self.item_frequency.items():
            result += frequency
        return result
    
    def size(self):
        """ Number of distinct feature values.

        :return: Number of distinct items/feature values
        :rtype: int
        """
        size = 0
        for _, frequency in self.item_frequency.items():
            size += frequency
        return size
    
    def width(self):
        """ Width of the cluster.
        
        :return: Width of the cluster.
        :rtype: int
        """
        return len(list(self.item_frequency.keys()))

class ClopeClustering(ClusteringAlgorithm):
    """ Implements CLOPE clustering algorithm.

    """

    def __init__(self, feature_dict, output_path, r=2):
        ClusteringAlgorithm.__init__(self, feature_dict, output_path)
        self.r = r

    def delta_add(self, cluster, feature_vector):
        """ Calculate delta add for the case feature vector is added to the 
        cluster.
        """
        s_new = cluster.size() + len(feature_vector)
        w_new = cluster.width()
        for _, feature in feature_vector.items():
            if feature not in list(cluster.item_frequency.keys()):
                w_new += 1
        c_n = (len(cluster.cluster_members))
        result = s_new * (c_n + 1) / pow(w_new, self.r) 
        result -= cluster.size() * c_n / pow(cluster.width(), self.r)
        return result
    
    def delta_rem(self, cluster, feature_vector):
        """ Calculate delta remove for the case feature vector is removed from
         the cluster.

         TODO: Maybe check what happens if feature vector is removed which was 
         not part of the cluster.
        """
        s_new = cluster.size() - len(feature_vector)
        w_new = cluster.width()
        for _, feature in feature_vector.items():
            if feature in list(cluster.item_frequency.keys()):
                if cluster.item_frequency[feature] > 0:
                    cluster.item_frequency[feature] -= 1
                if cluster.item_frequency[feature] == 0:
                    w_new -= 1

        c_n = (len(cluster.cluster_members))
        # we lose profit of the current cluster size ...
        result = -1 * cluster.size() * c_n / pow(cluster.width(), self.r)
        # ...but gain the profit of the cluster from which the vector was 
        # removed
        if w_new > 0:
            result += s_new * (c_n - 1) / pow(w_new, self.r) 
        return result

    def do_clustering(self):
        """Concrete implementation specific to the algorithm.

        For further details on the algorithm, read the class doc string.
        """
        # count occurence of features
        item_dict = dict()
        vector_cluster_dict = dict()

        # first iteration over all data
        for vector_id, feature_vector in self.feature_dict.items():
            max_profit_delta = 0
            best_cluster = None
            # iterate over all cluster to calculate respecitve add delta in 
            # profit
            for _, cluster in self.cluster_dict.items():
                delta = self.delta_add(cluster, feature_vector)
                if delta > max_profit_delta:
                    best_cluster = cluster
                    max_profit_delta = delta
            # delta in case a new cluster is created.  
            new_cluster = ClopeCluster()
            new_cluster.add(vector_id, feature_vector)
            # if we only have one vector in this cluster, delate will simply 
            # be 1 (the hight) devided by number of elements (features) in this
            # vector
            delta = 1 / pow(len(feature_vector), self.r)
            # add the respective cluster to the clustering. If we use the new 
            # cluster, we won't need to add the feature vector to it. If we use
            # a already existing cluster, wee need to add the feature vector to
            # it, as up until now we only calculated the delta from it.
            if delta > max_profit_delta:
                # set new cluster as cluster which yields the highest profit.
                best_cluster = new_cluster
            else:
                # if we use an existing cluster, add the feature vector to it.
                best_cluster.add(vector_id, feature_vector)
            # add the best cluster for this feature vector to the clustering
            vector_cluster_dict[vector_id] = best_cluster
            self.cluster_dict[best_cluster.uuid] = best_cluster

        # second iteration, move feature vectors between clusters to
        # achive the best clustering
        moved = True
        while moved == True:
            # we haven't moved any feature vectore yet.
            moved = False
            for vector_id, feature_vector in self.feature_dict.items():
                max_profit_delta = 0
                curr_cluster = vector_cluster_dict[vector_id]
                best_cluster = curr_cluster
                delta_offset = self.delta_rem(curr_cluster, feature_vector)
                # iterate over all cluster to calculate respecitve add delta in 
                # profit with respect to the remove delta (influence on profit 
                # when removing a feature vector from the current cluster)
                for _, cluster in self.cluster_dict.items():
                    # don't add to same cluster twice
                    delta = delta_offset
                    if vector_cluster_dict[vector_id] == cluster.uuid:
                        # if we don't modify anything, delta will be zero
                        delta = 0
                    else:
                        delta += self.delta_add(cluster, feature_vector)
                    if delta > max_profit_delta:
                        best_cluster = cluster
                        max_profit_delta = delta
                # delta in case a new cluster is created.
                new_cluster = ClopeCluster()
                delta = delta_offset
                # if we only have one vector in this cluster, delate will 
                # simply be 1 (the hight) devided by number of elements 
                # (features) in this vector
                delta += 1 / pow(len(feature_vector), self.r)
                # add the respective cluster to the clustering. If we use the
                # new cluster, we won't need to add the feature vector to it. 
                # If we use a already existing cluster, wee need to add the
                # feature vector to it, as up until now we only calculated the
                # delta from it.
                if delta > max_profit_delta:
                    # set new cluster as cluster which yields the highest 
                    # profit.
                    best_cluster = new_cluster
                    max_profit_delta = delta

                # move feature vector to the best cluster if neccessarry
                if best_cluster.uuid != curr_cluster.uuid:
                    # move vektor from cluster
                    best_cluster.add(vector_id, feature_vector)
                    curr_cluster.remove(vector_id, feature_vector)
                    # add to clustering if new cluster
                    if best_cluster.uuid == new_cluster.uuid:
                        self.cluster_dict[best_cluster.uuid] = best_cluster
                    moved = True

                # remove empty clusters
                len_of_curr_cluster = \
                    len(self.cluster_dict[curr_cluster.uuid].cluster_members)
                if len_of_curr_cluster < 1:
                    del self.cluster_dict[curr_cluster.uuid]