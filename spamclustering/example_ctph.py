import os
import sys

import spamclustering.algorithms.ctph as ctph

def main():
    """
    Performs clustering with the help of a context triggered piecewise hash
    function. Files found in `<path_to_files>` are processed, similar files
    are grouped in a cluster and the cluster is then written to
    `path_to_cluster_out`.

    Run with:
    
    python -m spamclustering.example_ctph <path_to_files> 
    <path_to_cluster_out>
    
    from root directory.
    """
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

        test_cluster = ctph.Ctph(file_list, out_path)
        test_cluster.do_clustering()
        test_cluster.write_cluster_to_disk()


if __name__ == "__main__":
    main()
