import sys
import os

from spamclustering.mailIo import mailIo as mailIo

import spamclustering.preprocess.extentedemailmessage as exm
import spamclustering.benchmarking.difftool as dt

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

        for cluster in cluster_set:
            for file_name,_ in cluster.invert().items():
                if file_name in file_dict.keys():
                    file_dict[file_name].append(cluster.uuid)
                else: 
                    file_dict[file_name] = [cluster.uuid]
        
        print('Total number of files:', len(file_dict.keys()))
        print('The following files were found in multiple clusters:')
        for file, cluster_list in file_dict.items():
            if len(cluster_list) > 1:
                print(file, cluster_list)        
    else:
        print("Path was not given")
if __name__ == "__main__":
    main()
