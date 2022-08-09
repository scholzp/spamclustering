import numpy
import pandas
import os

from collections import defaultdict


class Tree():
    value = ''
    sub_tree = None
    root = None

    def __init__(self, name, root=None):
        self.value = name
        self.sub_tree = []
        self.root = root

    def add_node(self, node):
        self.sub_tree.append(node)

    def print(self, depth=0):
        indent = depth * 2
        print(indent * ' ' + '| ' + str(self.value))
        print(indent * ' ' + '---')
        for tree in self.sub_tree:
            tree.print(depth + 1)

    def create_from_path(self, path):
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
                base.add_node(new_tree)
                jump_dict[complete_path] = new_tree
        return start

    def leaf_affinity(self, leaf_dict):
        if leaf_dict is None:
            leaf_dict = {}
        if self.sub_tree == []:
            leaf_dict[os.path.split(self.value)[1]] = self.root
        else:
            for sub_tree in self.sub_tree:
                sub_tree.leaf_affinity(leaf_dict)

    def generate_file_diff(self, other):
        # first get leaf affinities
        leaf_affinity_self = {}
        leaf_affinity_other = {}
        self.leaf_affinity(leaf_affinity_self)
        other.leaf_affinity(leaf_affinity_other)
        # invert them, create sets of file names
        affinity_self_inv = defaultdict(set)
        affinity_other_inv = defaultdict(set)
        {affinity_self_inv[c].add(f) for f, c in leaf_affinity_self.items()}
        {affinity_other_inv[c].add(f)
            for f, c in leaf_affinity_other.items()}

        set_all_other = set(leaf_affinity_other.values())
        set_all_self = set(leaf_affinity_self.values())
        # calculate rand index and create a 2d pandas data frame from the
        # results
        keys_other = affinity_other_inv.keys()
        keys_other_value = {c.value: c for c in keys_other}
        keys_self = affinity_self_inv.keys()
        keys_self_value = {c.value: c for c in keys_self}
        series_dict = {}
        global_tn = 0
        global_fn = 0
        global_tp = 0
        global_fp = 0
        for cluster in keys_self:
            files = affinity_self_inv[cluster]
            rand_index_list = []
            for cluster_o in keys_other:
                rand_index = 0
                files_o = affinity_other_inv[cluster_o]
                intersection = files & files_o
                true_positive = len(intersection)
                true_negative = len((set_all_self - files) &
                                    (set_all_other - files_o))
                false_positive = len(files_o - files)
                false_negative = len(files - files_o)
                global_tn += true_negative
                global_fn += false_negative
                global_tp += true_positive
                global_fp += false_positive
                rand_index = (true_positive + true_negative) / \
                             (false_positive + false_negative
                              + true_positive + true_negative)
                rand_index_list.append(rand_index)
            series_dict[cluster.value] = pandas.Series(rand_index_list,
                                                       keys_other_value.keys())

        columns_df = [c.value for c in keys_self]
        rand_frame = pandas.DataFrame(series_dict, columns=columns_df)
        # to make sure, that not multiple clusters get matched to a cluster of
        # the comparing set, we perform maxima search once for the original
        # data frame and once for the transformed one.
        imax = rand_frame.idxmax()
        imax_i = rand_frame.T.idxmax()
        match_dict = {}
        # first add all clusters which have a match somehow
        for (c, r) in imax.items():
            if rand_frame.at[r, c] > 0 and (r, c) in imax_i.items():
                match_dict[c] = r
        # then add all other clusters
        for key in (set(keys_self_value.keys()) - set(match_dict.keys())):
            match_dict[key] = 'missing'
        for key in (set(keys_other_value.keys()) - set(match_dict.values())):
            match_dict[key] = 'additional'

        for (key, value) in match_dict.items():
            additional_set = set()
            missing_set = set()
            new_value = ''
            if value == 'missing':
                k_self = keys_self_value[key]
                missing_set = affinity_self_inv[k_self]
            elif value == 'additional':
                k_other = keys_other_value[key]
                additional_set = affinity_other_inv[k_other]
            else:
                # generate delta
                k_self = keys_self_value[key]
                k_other = keys_other_value[value]
                additional_set = affinity_other_inv[k_other] - \
                    affinity_self_inv[k_self]
                missing_set = affinity_self_inv[k_self] - \
                    affinity_other_inv[k_other]
                new_value = value
            # create frankensteins dict for delta information...
            match_dict[key] = (new_value,
                               (('additional', additional_set.copy()),
                                ('missing', missing_set.copy())))
        # {key, value}
        #       \***/-----------------------------------------+
        #         |  index 0                                  | index 1
        #         v                                           v
        #       (Name of Match,                     (missing),  (additional))
        #                                               | index 0     |
        # (Keyword 'missing'   , set of missing files) <+             |
        # \********v*******/     \**********v********/                | index 1
        #        index 0                index 1                       |
        #  /*******^********\     /*********^***********\             |
        # (Keyword 'additional' , set of additional files)  <---------+

        # print this monster
        for (key, value) in match_dict.items():
            string = 'Matching ' + str(key) + ' against '
            if value[0] == '':
                string += 'HAS NO MATCH\n'
            else:
                string += str(value[0] + '.\n')
            if (len(value[1][0][1]) != 0) or (len(value[1][1][1]) != 0):
                string += 'Diffs:\n Missing: '
                for missing in value[1][0][1]:
                    string += str(missing) + '; '
                string += '\n Additional: '
                for additional in value[1][1][1]:
                    string += str(additional) + ';'
            string += '\n ----------------------------------- \n'
            print(string)
        print(global_tp, global_tn, global_fp, global_fn)
