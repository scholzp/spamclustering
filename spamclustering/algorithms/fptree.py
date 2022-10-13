import math
import copy

from scipy import stats as sps
from .clusteringalgorithm import ClusteringAlgorithm
from .spamcluster import SpamCluster


class FPTreeNode():
    """
    TODO: Check node purity

    """
    def __init__(self, min_size, root=False):
        self.children = []
        self.parent = None
        self.siblings = []
        self.feature = ''
        self.is_root = root
        self.id_list = []
        self.min_size = min_size

    def add_node(self, node):
        self.children.append(node)
        node.parent = self
    
    def search_feature(self, feature):
        result = None
        for child in self.children:
            if child.feature == feature:
                result = child 
        return result

    def add_feature_vector(self, mail_id, feature_vector):
        feature = feature_vector.pop(0)
        if len(feature_vector) == 0:
            self.id_list.append(mail_id)
            return
        else:
            feature_child = self.search_feature(feature)
            if feature_child is None:
                new_child = FPTreeNode(self.min_size)
                new_child.feature = feature
                self.add_node(new_child)
                feature_child = new_child
            feature_child.add_feature_vector(mail_id, feature_vector)
                
    
    def is_leaf(self):
        """ Return true if this node is a leaf.

        This is the case, if this node has no children.

        :return: False if this node has children, True otherwise
        :rtype: Boolean 
        """
        return (0 == len(self.children))

class FPTreeClustering(ClusteringAlgorithm):
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

    def __init__(self, feature_dict, output_path, min_size=5):
        ClusteringAlgorithm.__init__(self, feature_dict, output_path)
        self.min_size = min_size

    def do_clustering(self):
        """Concrete implementation specific to the algorithm.

        For further details on the algorithm, read the class doc string.
        """
        # create FPTree and perform clustering
        fp_tree = FPTreeNode(self.min_size, root=True)

        # count occurence of features
        item_dict = dict()
        for _, feature_vector in self.feature_dict.items():
            for feature, feature_value in feature_vector.items():
                if feature_value in item_dict.keys():
                    item_dict[feature_value] += 1
                else:
                    item_dict[feature_value] = 0

        # add the feature vector of each mail to the tree
        for mail_id, feature_vector in self.feature_dict.items():
            # sort feature values by number of occurence
            new_vec = list(feature_vector.values())
            new_vec.sort(key = (lambda h: item_dict[h]), reverse=True)
            fp_tree.add_feature_vector(mail_id, new_vec)

        #find leaves in the FpTree
        to_visit = fp_tree.children
        leaves = []
        while len(to_visit) > 0:
            current = to_visit.pop()
            if current.is_leaf():
                leaves.append(current)
            else:
                to_visit.extend(current.children)
        
        # create clusters form leaves
        for leave in leaves:
            cluster = SpamCluster()
            cluster.add(leave.id_list)
            self.cluster_dict[cluster.uuid] = cluster