import math
import copy

from scipy import stats as sps
from .clusteringalgorithm import ClusteringAlgorithm
from .spamcluster import SpamCluster


class CCTreeNode():
    """
    TODO: Check node purity

    """
    def __init__(self, purity_threshold, data_points):
        self.children = []
        self.data_points = data_points
        self.purity_threshold = purity_threshold
    
    def do_clustering(self):
        # retrieve keys of attribute-value dict from the first mail
        first_id = list(self.data_points.keys())[0]
        list_of_attributes = self.data_points[first_id].keys()
        # create a dict of values and their absolut frequency
        # for each attribute
        attribute_value_dict = dict()
        # iterate over all attributes availble
        for attribute in list_of_attributes:
            value_dict = dict()
            # process data point per attributes, this means process values of
            # the given attribute for each data point
            for _, data_point in self.data_points.items():
                # the conrecte value of the chosen attribute is the value of
                # the data_point's dict with attribute as index
                value = data_point[attribute]
                # frequency of occurences of the value over different data
                # points will be counted
                if value in value_dict.keys():
                    value_dict[value] += 1
                else:
                    value_dict[value] = 1
            # update the attribute dict with a dict {value:count}
            # result structure looks like:
            #   {attribute : {value1:count, value2:count, ...}, atribute2: ...}
            attribute_value_dict[attribute] = value_dict
        # if node purity is to low, split on attribute with highest entropy
        node_purity = self._calculate_node_purity(attribute_value_dict)
        if self.purity_threshold > node_purity:
            splitting_attribute = self._calculute_max_shannon_entropy(
                                            attribute_value_dict)
            if splitting_attribute == '':
                return
            # to split the tree, we must split on the attribute with highest
            # entropy. All data_points sharing the same value for this
            # attribute will be part of the same childnode. An all points with
            # different values for this point, will be part of a different
            # child node.
            # Create a dict which stores information about which points belong 
            # to which value:
            # {value1: [point1_1, point1_2, ...], value2:[point2_1, ...], ...}
            splitting_dict = dict()
            #print('Splitting at attribute: ', splitting_attribute)
            for point_id, data_point in self.data_points.items():
                value_of_point = data_point[splitting_attribute]
                data_point_copy = copy.deepcopy(data_point)
                data_point_copy.pop(splitting_attribute)
                if value_of_point in splitting_dict:
                    splitting_dict[value_of_point] |= {point_id: 
                                                        data_point_copy}
                else:
                    splitting_dict[value_of_point] = {point_id: 
                                                      data_point_copy}
            # create child nodes
            for _, point_list in splitting_dict.items():
                new_node = CCTreeNode(self.purity_threshold, point_list)
                self.children.append(new_node)
                new_node.do_clustering()
        else:
            return

    def _calculate_node_purity(self, attribute_value_dict):
        node_purity = 0
        num_of_data_points = len(self.data_points)
        for attribute, values in attribute_value_dict.items():
            for value, num_data_respecting_value in values.items():
                # p_vji, see definition (1) in paper
                p_vji = num_data_respecting_value / num_of_data_points
                node_purity += p_vji * math.log(p_vji)
        node_purity *= -1
        return node_purity

    def _calculute_max_shannon_entropy(self, attribute_value_dict):
        highest_entropy = 0
        attribute_of_highest_entropy = ''
        total_values_count = len(attribute_value_dict)
        for attribute, value_dict in attribute_value_dict.items():
            # create a list to calculate entropy from
            frequency_list = []
            for _, value_occurence in value_dict.items():
                frequency_list.append(value_occurence / total_values_count)
            entropy_of_attribute = sps.entropy(frequency_list)
            if entropy_of_attribute > highest_entropy:
                highest_entropy = entropy_of_attribute
                attribute_of_highest_entropy = attribute
        return attribute_of_highest_entropy

    def is_leaf(self):
        """ Return true if this node is a leaf.

        This is the case, if this node has no children.

        :return: False if this node has children, True otherwise
        :rtype: Boolean 
        """
        return (0 == len(self.children))

class CcTreeClustering(ClusteringAlgorithm):
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

    def __init__(self, feature_dict, output_path, purity_threshold=50):
        ClusteringAlgorithm.__init__(self, feature_dict, output_path)
        self.purity_threshold = purity_threshold

    def do_clustering(self):
        """Concrete implementation specific to the algorithm.

        For further details on the algorithm, read the class doc string.
        """
        # create ccTree and perform clustering
        ccTree = CCTreeNode(self.purity_threshold, self.feature_dict)
        ccTree.do_clustering()

        #find leaves in the CCTree
        to_visit = [ccTree]
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
            cluster.add([file_id for file_id, _ in leave.data_points.items()])
            self.cluster_dict[cluster.uuid] = cluster