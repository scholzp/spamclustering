import os
import uuid
import shutil

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
