import os
import uuid
import shutil

DEEPCOPY = False


class ClusterDiff:
    """Helper class for storing diff statistics of two clusters.
    :param cluster_one: First cluster from which this diff is created.
    :type cluster_one: :class:`spamcluster.algorithms.spamcluster.SpamCluster`
    :param cluster_two: Second cluster from which this diff is created.
    :type cluster_two: :class:`spamcluster.algorithms.spamcluster.SpamCluster`
    :param missing_set: Set of filenames missing in the second set.
    :type missing_set: set() of strings
    :param additional_set: Set of filenames not contained in the first cluster
        but in th second.
    :type addtional_set: set() of string
    """
    def __init__(self, cluster_one, cluster_two, missing_set, additional_set):
        self.cluster_one = cluster_one
        self.cluster_two = cluster_two
        set1 = cluster_one.cluster_members
        set2 = cluster_two.cluster_members
        self.true_positive = set2 & set1
        self.false_positive = set2 - set1
        self.false_negative = set1 - set2

    def __str__(self):
        result = ''
        result += 'Diff of {0} against {1}'.format(self.cluster_one.uuid,
                                                   self.cluster_two.uuid)
        result += '\nMissing:\n'
        for missing in self.false_negative:
            result += missing + '; '
        result += '\nAdditional:\n'
        for additional in self.false_positive:
            result += additional
        return result


class SpamCluster:
    """ Helper class which stores cluster information.

    :param uuid: UUID of this
        :class:`spamclustering.algorithms.ctph.Spamcluster`.
    :type uuid: str
    :param cluster_members: Set of filenames representing files added to this
        cluster
    :type cluster_members: set of str
    """
    def __init__(self):
        self.uuid = str(uuid.uuid4())
        self.cluster_members = set()

    def add(self, files):
        """ Add files to the cluster.
        This function will append the given file(s) to the cluster's file list.

        :param files: Set of file names to add to this cluster, or a string
            for a single file.
        :type files: str, set of str
        """
        if files is None:
            pass

        if isinstance(files, list):
            self.cluster_members |= set(files)
        else:
            self.cluster_members.add(files)

    def write_to_path(self, path):
        """ Write this cluster to the desired path.

        The destination path was stated when calling the constructor. Within
        this path, a directory will be created with the UUID of this cluster as
        name. All files belonging to this cluster will either be copied or
        respective symbolic links will created.
        """
        cluster_path = os.path.join(path, self.uuid)
        if not os.path.isdir(cluster_path):
            os.mkdir(cluster_path)
        for source_file in self.cluster_members:
            file_dest = os.path.join(cluster_path, os.path.split(
                                                            source_file)[1])
            abs_path_source = os.path.abspath(source_file)
            if DEEPCOPY is True:
                shutil.copy(abs_path_source, file_dest)
            else:
                os.symlink(abs_path_source, file_dest)

    def invert(self):
        """ Inverts the cluster in a way, that the cluster-file relationship is
        turned into a file-cluster relationship. This means, the returned dict
        will have the members as keys and the respective cluster as value.

        :return: Structure which represent file-cluster relationship instead of
            cluster-file relationship.
        :rtype: dict with str as keys, cluster as value
        """
        result = {}
        for file in self.cluster_members:
            result[file] = self
        return result

    def compare(self, other):
        """Compares this cluster against another cluster. And calculates the
        diff from both.

        :param other: Cluster to compare to.
        :type other:
            :class:`spamclustering.algorithms.spamclauster.Spamcluster`
        :return: Difference of both clusters.
        :rtype:
            :class:`spamclustering.algorithms.spamclauster.ClusterDiff`
        """
        result = None
        if other is not None:
            missing_set = self.cluster_members - other.cluster_members
            additional_set = other.cluster_members - self.cluster_members
            result = ClusterDiff(self, other, missing_set, additional_set)
        return result
