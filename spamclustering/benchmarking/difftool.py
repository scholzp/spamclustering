import pandas
import os

from sklearn import metrics

from ..algorithms import spamcluster as sc


class Tree():
    value = ''
    sub_tree = None
    root = None

    def __init__(self, name, root=None):
        self.value = name
        self.sub_tree = []
        self.root = root
        self.is_file = False

    def add_node(self, node):
        """Add a subtree to this node.

        :param node: Node to add to this node.
        :type node: :class:`spamclustering.benchmarking.difftool.Tree`
        """
        self.sub_tree.append(node)

    def print(self, depth=0):
        """Print a recursive string representation of this tree.
        :param depth: Depth of the tree, when processing recursively.
        :type depth: int
        """
        indent = depth * 2
        print(indent * ' ' + '| ' + str(self.value))
        print(indent * ' ' + '---')
        for tree in self.sub_tree:
            tree.print(depth + 1)

    def create_from_path(self, path):
        """Beginning from `path`, traverse all subdirectories to find files.
        Create a tree structure to represent the fiel structure.

        :param path: Path from which the a directory tree is to be created.
        :type path: str
        :return: Starting node of the resulting tree.
        :rtype: :class:`spamclustering.benchmarking.difftool.Tree`
        """
        jump_dict = {}
        start = None
        for root, dirs, files in os.walk(path):
            base = None
            if root in jump_dict.keys():
                base = jump_dict[root]
            else:
                base = Tree(root)
                start = base
                jump_dict[root] = base
            contents = dirs + files
            for directory in contents:
                complete_path = os.path.join(root, directory)
                new_tree = Tree(complete_path, base)
                if os.path.isfile(complete_path):
                    new_tree.is_file = True
                base.add_node(new_tree)
                jump_dict[complete_path] = new_tree
        return start

    def to_cluster_set(self):
        """ Generates clusters from a file tree.
        :return: Set of clusters generated from the directory tree.
        :rtype: set() of
            :class:spamclustering.algorithms.spamcluster.SpamCluster
        """
        result = set()
        return self._generate_clusters(result)

    def _generate_clusters(self, cluster_set=None):
        """Help function to recursively traverse the directory tree. Generates
        cluster for each directory containing no subdirectories.
        """
        cluster = sc.SpamCluster()
        has_subdirs = False
        for sub_tree in self.sub_tree:
            if sub_tree.is_file is True:
                cluster.add(os.path.split(sub_tree.value)[1])
            else:
                has_subdirs = True
                sub_tree._generate_clusters(cluster_set)
        cluster.uuid = self.value
        if has_subdirs is False:
            cluster_set.add(cluster)
        return cluster_set

    def generate_file_diff(self, other):
        series_dict = {}
        # Create dicts which match cluster ids against cluster for faster
        # search
        self_clusters = {c.uuid: c for c in self.to_cluster_set()}
        other_clusters = {c.uuid: c for c in other.to_cluster_set()}
        # generate two sets, each containing all files for each cluster set
        set_all_self = set(cluster for _, cluster in self_clusters.items())
        set_all_other = set(cluster for _, cluster in other_clusters.items())
        # create a list which can be used as index for a pandas series
        df_index_self = list(self_clusters.keys())
        df_index_other = list(other_clusters.keys())
        for uuid in df_index_self:
            files = self_clusters[uuid].cluster_members
            rand_index_list = []
            for uuid_o in df_index_other:
                files_o = other_clusters[uuid_o].cluster_members
                true_positive = len(files & files_o)
                true_negative = len((set_all_self - files) &
                                    (set_all_other - files_o))
                false_positive = len(files_o - files)
                false_negative = len(files - files_o)
                rand_index = (true_positive + true_negative) / \
                             (false_positive + false_negative
                              + true_positive + true_negative)
                rand_index_list.append(rand_index)
            series_dict[uuid] = pandas.Series(rand_index_list, df_index_other)

        rand_frame = pandas.DataFrame(series_dict, columns=df_index_self)
        # to make sure, that not multiple clusters get matched to a cluster of
        # the comparing set, we perform maxima search once for the original
        # data frame and once for the transformed one.
        imax = rand_frame.idxmax()
        imax_i = rand_frame.T.idxmax()
        match_dict = {}
        # first add all clusters which have a match somehow
        for (column, row) in imax.items():
            if (rand_frame.at[row, column] > 0) and \
               ((row, column) in imax_i.items()):
                match_dict[column] = row
        # then add all other clusters and mark them by a keyword
        for uuid in (set(df_index_self) - set(match_dict.keys())):
            match_dict[uuid] = 'missing'
        for uuid in (set(df_index_other) - set(match_dict.values())):
            match_dict[uuid] = 'additional'
        # generate diffs and some statistics
        num_tp = 0
        num_tn = 0
        num_fp = 0
        num_fn = 0
        set_all_files = set()
        for _, cluster in self_clusters.items():
            set_all_files |= cluster.cluster_members
        for (uuid, match_uuid) in match_dict.items():
            if match_uuid == 'missing':
                print('No match found for cluster', uuid)
                num_fn += len(self_clusters[uuid].cluster_members)

            elif match_uuid == 'additional':
                print('Generated completely new cluster', uuid)
                num_fp += len(other_clusters[uuid].cluster_members)
            else:
                cluster_match = other_clusters[match_uuid]
                cluster_gold = self_clusters[uuid]
                cluster_diff_obj = cluster_gold.compare(cluster_match)
                num_tp += len(cluster_diff_obj.true_positive)
                num_tn += len((set_all_files - cluster_gold.cluster_members) &
                              (set_all_files - cluster_match.cluster_members))
                num_fp += len(cluster_diff_obj.false_positive)
                num_fn += len(cluster_diff_obj.false_negative)
                print(cluster_diff_obj)
            print('-------------------------------------------------------')
        print('tn={}, fn={}, tp={}, fp={}, n={}'.format(
                            num_tn, num_fn, num_tp, num_fp,
                            len(set_all_files)))
        print('Cluster num gold: {}, Cluster num algo: {}.'.format(
                len(df_index_self), len(df_index_other)))

        labels_gold = []
        labels_test = []
        # assign a label to each cluster. Only store the label for scipy's rand
        # score implementation
        label = 0
        for (uuid, match_uuid) in match_dict.items():
            if match_uuid == 'missing':
                labels_gold += [label] * len(self_clusters[
                                                 uuid].cluster_members)
            elif match_uuid == 'additional':
                labels_test += [label] * len(other_clusters[
                                                 uuid].cluster_members)
            else:
                labels_gold += [label] * len(self_clusters[
                                                 uuid].cluster_members)
                labels_test += [label] * len(other_clusters[
                                                 match_uuid].cluster_members)
            label += 1
        print('Rand score: ', metrics.rand_score(labels_gold, labels_test))
