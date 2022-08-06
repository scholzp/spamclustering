import sys
import os
import uuid
import shutil
import ssdeep


DEEPCOPY = False


class SpamCluster:
    """ Helper class which stores cluster information.

    :param uuid: UUID of this
        :class:`spamclustering.algorithms.ctph.Spamcluster`.
    :type uuid: :class:`uuid.uuid`
    :param path: Path to where this cluster is to be written to.
    :type path: str
    :param cluster_members: List of filenames representing files added to this
        cluster
    :type cluster_members: list of str
    """
    def __init__(self, path):
        self.path = path
        self.uuid = uuid.uuid4()
        self.cluster_members = []

    def add(self, files):
        """ Add files to the cluster.
        This function will append the given file(s) to the cluster's file list.
        
        :param files: List of file names to add to this cluster, or a string
            for a single file.
        :type files: str, list of str
        """
        if files is None:
            pass

        if isinstance(files, list):
            self.cluster_members.append(files)
        else:
            self.cluster_members.append(files)

    def write_to_path(self):
        """ Write this cluster to the desired path.

        The destination path was stated when calling the constructor. Within
        this path, a directory will be created with the UUID of this cluster as
        name. All files belonging to this cluster will either be copied or
        respective symbolic links will created.
        """
        cluster_path = os.path.join(self.path, str(self.uuid))
        if not os.path.isdir(cluster_path):
            os.mkdir(cluster_path)
        for source_file in self.cluster_members:
            file_dest = os.path.join(cluster_path, os.path.split(
                                                            source_file)[1])
            if DEEPCOPY is True:
                shutil.copy(source_file, file_dest)
            else:
                os.symlink(source_file, file_dest)
        if len(self.cluster_members) > 1:
            print(self.uuid)


class ClusteringAlgorithm:
    """Base class for clustering algorithms.

    Implements some boiler plate code for writing clusters to disk.
    """
    def __init__(self, input_list, output_path):
        """ Constructor which should be used for this class.
        Providing the required arguments will result in a ready to use
        algorithm, which can do the clustering and is able to write the results
        back to disk.

        :param input_list: List of file names to process.
        :type input_list: str or list of str
        :param output_path: Path to the location to which all cluster should be
            written to.
        :type output_path: str
        """
        self.input_files = input_list
        self.output_path = output_path
        self.input_path = ''
        self.cluster_dict = {}

    def do_clustering(self):
        """ Performs the class specific clustering algorithm.

        The base class creates one cluster and adds all items to this cluster.
        This function is to be overwritten by classes which inherited from
        ClusteringAlgorithm and implement own clustering algorithms.
        """
        new_cluster = SpamCluster(self.output_path)
        new_cluster.add(self.input_files)
        self.cluster_dict[new_cluster.uuid] = new_cluster

    def write_cluster_to_disk(self):
        """ Writes all clusters in cluster_dict to disk.

        Path is specified through self.output_path, which was set when calling
        the respective constructor. Needs to be set otherwise.
        """
        for cluster_id in self.cluster_dict.keys():
            self.cluster_dict[cluster_id].write_to_path()


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

    def __init__(self, input_list, output_path, threshold=85):
        ClusteringAlgorithm.__init__(self, input_list, output_path)
        self.threshold_value = threshold

    def do_clustering(self):
        """Concrete implementation specific to the algorithm.

        For further details on the algorithm, read the class doc string.
        """
        # dict to store hash values of each file
        hash_dict = {}
        # calculate hash value for each file
        for file in self.input_files:
            hash_dict[file] = ssdeep.hash_from_file(file)

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
                cluster = SpamCluster(self.output_path)
                cluster.add(current)
                self.cluster_dict[cluster.uuid] = cluster
            file_cluster_dict[current] = cluster


def main():
    argv = sys.argv
    argc = len(sys.argv)
    if argc > 0:
        print('This script was started as main for debugging purposes.')
        print('Using "', argv[1], '"as input.')
        fn = argv[1]
        file_list = []
        out_path = ''
        if os.path.isdir(fn):
            print('Input is directory...')
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
