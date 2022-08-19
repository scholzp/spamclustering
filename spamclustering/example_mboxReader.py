from optparse import OptionParser
import os

import spamclustering.mboxReader.mboxToEml as mb


def main():
    """ Example showing how to use contents of mboxToEml package.
    
    This script reads a file in `MBox` format and extracts the respective `eml`
    files. These files are then stored at the given path.
    Run with:
    
    python -m spamclustering.example_mboxReader -i <path_to_mbox>/file.mbox -o 
    <path_to_output_dir> 
    
    from root directory
    """
    usage = "usage %prog [options] arg"
    parser = OptionParser(usage)
    parser.add_option("-i", "--input", dest="ifFilename",
                      help="Specifies file to process")
    parser.add_option("-o", "--output", dest="ofFilename",
                      help="Specifies directory to write results to")
    parser.add_option("-d", "--directory", dest="isDir",
                      help="Specifies if input is a directoy." +
                           "If set, the program will process all files" +
                           "in the directory. Not recursive, no " +
                           "subdirectories will be searched.", default="False")

    (opts, args) = parser.parse_args()
    inFile = opts.ifFilename
    ofFile = opts.ofFilename
    isDir = opts.isDir

    if not os.path.isfile(inFile):
        print("Error: File", inFile, "does not exist or is an directory.",
              "Inlcude -d switch if it's a directoy")
        return 1

    if os.path.isdir(ofFile):
        print("Warning: ", ofFile, "does already exist")

    if isDir == "True":
        print("Process dir")
        print("Not implemented yet! Run for each file without -d switch!")
        return 0
    elif isDir == "False":
        mb.processMbox(inFile, ofFile)


if __name__ == "__main__":
    main()
