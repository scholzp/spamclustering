import sys
import os
import uuid
import shutil
import ssdeep


class SpamCluster:
    uuid = None
    path = ''
    cluster_members = list()

    def __init__(self, path):
        self.path = path
        self.uuid = uuid.uuid4()
        self.cluster_members = []

    def add(self, files):
        if isinstance(files, list):
            self.cluster_members.append(files)
        else:
            self.cluster_members.append(files)

    def write_to_path(self):
        cluster_path = os.path.join(self.path, str(self.uuid))
        if not os.path.isdir(cluster_path):
            os.mkdir(cluster_path)
            _ = 1 + 2
        for source_file in self.cluster_members:
            file_dest = os.path.join(cluster_path, os.path.split(
                                                            source_file)[1])
            shutil.copy(source_file, file_dest)
        if len(self.cluster_members) > 1:
            print(self.uuid)


class ClusteringAlgorithm:
    input_files = list()
    cluster_dict = dict()
    input_path = ''
    output_path = ''

    def __init__(self, input_list, output_path):
        self.input_files = input_list
        self.output_path = output_path

    def do_clustering(self):
        new_cluster = SpamCluster(self.output_path)
        new_cluster.add(self.input_files)
        self.cluster_dict[new_cluster.uuid] = new_cluster

    def write_cluster_to_disk(self):
        for cluster_id in self.cluster_dict.keys():
            self.cluster_dict[cluster_id].write_to_path()


class Ctph(ClusteringAlgorithm):
    threshold_value = 85

    def __init__(self, input_list, output_path):
        ClusteringAlgorithm.__init__(self, input_list, output_path)

    def do_clustering(self):
        hash_dict = dict()
        for file in self.input_files:
            hash_dict[file] = ssdeep.hash_from_file(file)
        file_cluster_dict = dict()
        for current in hash_dict.keys():
            best_match = ('', 0)
            for comp in hash_dict.keys():
                if current != comp:
                    match_degree = ssdeep.compare(hash_dict[current],
                                                  hash_dict[comp])
                    if (match_degree > self.threshold_value) and \
                       (match_degree > best_match[1]):
                        best_match = (comp, match_degree)

            cluster = None
            if best_match[0] in file_cluster_dict.keys():
                cluster = file_cluster_dict[best_match[0]]
                cluster.add(current)
            else:
                cluster = SpamCluster(self.output_path)
                cluster.add(current)
                self.cluster_dict[cluster.uuid] = cluster
            file_cluster_dict[current] = cluster
        print('Created ', len(self.cluster_dict.keys()), 'clusters')


def main():
    argv = sys.argv
    argc = len(sys.argv)
    if argc > 0:
        print('This script was started as main for debuging purposes.')
        print('Using "', argv[1], '"as input.')
        fn = argv[1]
        file_list = list()
        out_path = ''
        if os.path.isdir(fn):
            print('Input is directoy...')
            file_list = filter(lambda i: (os.path.splitext(i)[1] == '.eml'),
                               os.listdir(fn))
            file_list = [os.path.join(fn, file) for file in file_list]
        else:
            file_list = [fn]
        if len(argv) > 2:
            out_path = argv[2]
            if os.path.isdir(out_path):
                print('Writing output to', out_path)
            else:
                create = input(out_path + ' does not exist. Create? [y|n]')
                if create == 'y':
                    os.mkdir(out_path)

        test_cluster = Ctph(file_list, out_path)
        test_cluster.do_clustering()
        test_cluster.write_cluster_to_disk()


if __name__ == "__main__":
    main()
