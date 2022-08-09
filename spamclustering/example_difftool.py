import sys
import os

import spamclustering.benchmarking.difftool as diff

def main():
    """Compare both given directories and tries to find matches betweeen
    clusters (e.g. subdirectories of the given directories). These matches are
    later compared and diffs between the gold standard and the directory to
    compare are listed on directory basis.
    
    Run with:
    
    python -m spamclustering.example_difftool <path_gold_standard> 
    <path_to_compare>
    
    from root directory
    """
    argv = sys.argv
    argc = len(sys.argv)
    if argc > 0:
        print('This script was started as main for debugging purposes.')
        print('Using "', argv[1], '"as input.')
        fn = argv[1]
        file_list = []
 
        tree = diff.Tree(fn)
        start = tree.create_from_path(fn)

        if os.path.isdir(fn):
            print('Input is directory...')
            file_list = filter(lambda i: (os.path.splitext(i)[1] == '.eml'),
                               os.listdir(fn))
            file_list = [os.path.join(fn, file) for file in file_list]
        else:
            file_list = [fn]
        if len(argv) > 2:
            tree2 = diff.Tree(argv[2])
            start2 = tree2.create_from_path(argv[2])
            start.generate_file_diff(start2)

if __name__ == "__main__":
    main()
