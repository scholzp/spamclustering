import sys
import os

from spamclustering.mailIo import mailIo as mailIo

import spamclustering.preprocess.extentedemailmessage as exm
import spamclustering.preprocess.featureselector as fs

def main():
    """This example script takes a directory as input. From this directory 
    clusters will be created, which are later checked for duplicates. (A 
    dumplicate is a file contained by two or more different clusters).

    All duplicates will be printed.

    Run with:
    
    python -m spamclustering.example_featureSelection <path_to_eml>
    
    from project root directory.
    """
    argv = sys.argv
    argc = len(sys.argv)
    if argc > 0:
        print('This script was started as main for debugging purposes.')
        print('Using "', argv[1], '"as input.')
        fn = argv[1]
        directory_tree = None
        if os.path.isfile(fn):
            message = mailIo.readMailFromEmlFile(fn)
            _, file_id = os.path.split(fn)
            extMessage = exm.ExtentedEmailMessage(message, file_id)
            extMessage.extract_payload()
            featureSelector = fs.FeatureSelector([extMessage])
            featureSelector.toggle_feature('serialized_string')
            #print(featureSelector)
        else:
            print('Input was ot a file! Aborting!')
            return     
    else:
        print("Path wass not given")


if __name__ == "__main__":
    main()
