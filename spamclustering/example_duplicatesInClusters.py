import sys
import os

from spamclustering.mailIo import mailIo as mailIo

import spamclustering.preprocess.extentedemailmessage as exm
import spamclustering.benchmarking.difftool as dt
import spamclustering.benchmarking.clusteringprofiler as cp

def main():
    """This example script takes a directory as input. From this directory 
    clusters will be created, which are later checked for duplicates. (A 
    dumplicate is a file contained by two or more different clusters).

    All duplicates will be printed.

    Run with:
    
    python -m spamclustering.example_duplicatesInClusters <path>
    
    from project root directory.
    """
    argv = sys.argv
    argc = len(sys.argv)
    if argc > 0:
        print('This script was started as main for debugging purposes.')
        print('Using "', argv[1], '"as input.')
        fn = argv[1]
        directory_tree = None
        if os.path.isdir(fn):
            print('Input is directory...')
            directory_tree = dt.Tree(fn)
            directory_tree = directory_tree.create_from_path(fn)
        else:
            print('Input has to be directory path! Aborting!')
            pass
        cluster_set = directory_tree.to_cluster_set()
        file_dict = {}
        profiler = cp.ClusteringProfiler(cluster_set)
        print(profiler)        
    else:
        print("Path wass not given")


if __name__ == "__main__":
    main()
