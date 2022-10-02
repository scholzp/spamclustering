import os
import sys

import spamclustering.algorithms.ctph as ctph
import spamclustering.mailIo.mailIo as mailIo
import spamclustering.preprocess.extentedemailmessage as exm
import spamclustering.preprocess.featureselector as fs

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

        #create objects of class extendedEmailMessage from input files
        list_of_messages = []
        error_log = []
        count = 1
        list_len = len(file_list)
        for file in file_list:
            print('[{0}|{1}] Processing {2}'.format(count, list_len, file))
            try:
                message = mailIo.readMailFromEmlFile(file)
                _, message_id = os.path.split(file) 
                extMessage = exm.ExtentedEmailMessage(message, message_id)
                extMessage.extract_payload()
                list_of_messages.append(extMessage)
            except UnicodeEncodeError as u_error:
                error_string = \
                    'Mail {} is ill formed and therefore skipped!'.format(file)
                error_log += error_string + str(u_error) + '\n'
                print(error_string)
            except ValueError as v_error:
                error_string = \
                    'Mail {} produced a ValueError:{}'.format(file,
                                                              str(v_error))
                error_log += error_string + '\n'
                error_log += "Content of mail:\n"
                error_log += str(extMessage.header_dict) + '\n'
                print(error_string)
            count += 1
        print('Generate feature list ...')
        featureSelector = fs.FeatureSelector(list_of_messages)
        print('Peform clustering ...')
        test_cluster = ctph.Ctph(featureSelector.feature_list, out_path)
        test_cluster.do_clustering()
        print('Write clustering to disk ...')
        test_cluster.write_cluster_to_disk()


if __name__ == "__main__":
    main()
