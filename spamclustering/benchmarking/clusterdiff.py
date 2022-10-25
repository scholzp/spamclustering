import pandas
import os

from sklearn import metrics


def generate_cluster_diff(first, second):
    series_dict = {}
    # Create dicts which match cluster ids against cluster for faster
    # search
    self_clusters = {c.uuid: c for c in first}
    other_clusters = {c.uuid: c for c in second}
    # generate two sets, each containing all files for each cluster set
    set_all_self = set(cluster for _, cluster in self_clusters.items())
    set_all_other = set(cluster for _, cluster in other_clusters.items())
    # create a list which can be used as index for a pandas series
    df_index_self = list(self_clusters.keys())
    df_index_other = list(other_clusters.keys())
    for uuid in df_index_self:
        files = self_clusters[uuid].set_of_member_ids()
        rand_index_list = []
        for uuid_o in df_index_other:
            files_o = other_clusters[uuid_o].set_of_member_ids()
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
    #        print('No match found for cluster', uuid)
            num_fn += len(self_clusters[uuid].set_of_member_ids())

        elif match_uuid == 'additional':
    #        print('Generated completely new cluster', uuid)
            num_fp += len(other_clusters[uuid].set_of_member_ids())
        else:
            cluster_match = other_clusters[match_uuid]
            cluster_gold = self_clusters[uuid]
            cluster_diff_obj = cluster_gold.compare(cluster_match)
            num_tp += len(cluster_diff_obj.true_positive)
            num_tn += len((set_all_files - cluster_gold.cluster_members) &
                            (set_all_files - cluster_match.cluster_members))
            num_fp += len(cluster_diff_obj.false_positive)
            num_fn += len(cluster_diff_obj.false_negative)
            #print(cluster_diff_obj)
    #    print('-------------------------------------------------------')
    #print('tn={}, fn={}, tp={}, fp={}, n={}'.format(
                        # num_tn, num_fn, num_tp, num_fp,
                        # len(set_all_files)))
    #print('Cluster num gold: {}, Cluster num algo: {}.'.format(
    #        len(df_index_self), len(df_index_other)))

    labels_gold_dict = dict()
    labels_test_dict = dict()
    # assign a label to each cluster. Only store the label for scipy's rand
    # score implementation
    label = 0
    for (uuid, match_uuid) in match_dict.items():
        if match_uuid == 'missing':
            labels_gold_dict |= { member:label
                for member in self_clusters[uuid].set_of_member_ids()}

        elif match_uuid == 'additional':
            labels_test_dict |= { member:label
                for member in other_clusters[uuid].set_of_member_ids()}
        else:
            labels_test_dict |= { member:label
                for member in other_clusters[match_uuid].set_of_member_ids()}
            labels_gold_dict |= { member:label
                for member in self_clusters[uuid].set_of_member_ids()}
        label += 1
    
    labels_gold = []
    labels_test = []

    # add labels in the same order ot the label vectors
    for member_id, label in labels_test_dict.items():
        labels_test.append(label)
        labels_gold.append(labels_gold_dict[member_id])

    metrics_dict = {
        'ri' : metrics.rand_score(labels_gold, labels_test),
        'ari' : metrics.adjusted_rand_score(
            labels_gold, labels_test),
        'mmi' : metrics.normalized_mutual_info_score(labels_gold, labels_test),
        'ami' : metrics.adjusted_mutual_info_score(labels_gold, labels_test),
        'accuracy' : metrics.accuracy_score(labels_gold, labels_test),
        'precision' : metrics.precision_score(labels_gold, labels_test),
        'recall' : metrics.recall_score(labels_gold, labels_test), 
        'f1_macro' : metrics.f1_score(
            labels_gold, labels_test, average='macro'),
        'f1_micro' : metrics.f1_score(
            labels_gold, labels_test, average='micro'),
    }
    

    #print('Rand score: ', metrics.rand_score(labels_gold, labels_test))
    return metrics_dict