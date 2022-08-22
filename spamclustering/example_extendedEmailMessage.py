import sys
import os

from spamclustering.mailIo import mailIo as mailIo

import spamclustering.preprocess.extentedemailmessage as exm

def main():
    """This example script will take a single file as input from which it will
    try to generate a extendedEmailMessage object. The object will be printed.

    Run with:
    
    python -m spamclustering.example_extendedEmailMessage <path_to_eml>
    
    from project root directory.
    """
    argv = sys.argv
    argc = len(sys.argv)
    if argc > 0:
        print('This script was started as main for debugging purposes.')
        print('Using "', argv[1], '"as input.')
        fn = argv[1]
        file_list = list()
        if os.path.isdir(fn):
            print('Input is directory...')
            file_list = filter(lambda i: (os.path.splitext(i)[1] == '.eml'),
                               os.listdir(fn))
            file_list = [os.path.join(fn, file) for file in file_list]
        else:
            file_list = [fn]
        list_len = len(file_list)
        for file in file_list:
            # TODO: Converting mails currently can produce UnicodeEncodeError
            # and ValueError exceptions. This should be fixed someday. Unitl
            # then we need to deal with these exceptions in a defined way
            # without interrupting the whole script.
            message = mailIo.readMailFromEmlFile(file)
            extMessage = exm.ExtentedEmailMessage(message)
            extMessage.extract_payload()
            print(extMessage)
            print(("=================== END OF MAIL {} " +
                   "=========================").format(file))
    else:
        print("Path was not given")
if __name__ == "__main__":
    main()
