import sys

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
        # TODO: Converting mails currently can produce UnicodeEncodeError
        # and ValueError exceptions. This should be fixed someday. Unitl
        # then we need to deal with these exceptions in a defined way
        # without interrupting the whole script.
        message = mailIo.readMailFromEmlFile(fn)
        extMessage = exm.ExtentedEmailMessage(message)
        extMessage.extract_payload()
        print(extMessage)


if __name__ == "__main__":
    main()
