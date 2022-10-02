import sys
import os

from spamclustering.mailIo import mailIo as mailIo

import spamclustering.preprocess.extentedemailmessage as exm
import spamclustering.preprocess.mailanonymizer as ano


def main():
    """The example script will take a directory or single file as input 
    argument via `<path_to_dir1>`. After performing the necessary anonymization
    steps, the resulting `eml` files will be written to `<path_to_result>`.
    Optional arguments are a list of domains to block and a flag, which
    controls if the error log is written to a file. If both present, the
    `block list` must be the third argument. `block list` can be omitted, but
    this might produce errors. The log flag is either `True` or `False`, while
    `False` is the default value. Setting `log=True` will result in a text
    file named `error_log.txt` located at `<path_to_result>`.

    Run with:
    
    python -m spamclustering.example_anonymizer <path_to_dir1>
    <path_to_result> tests/domains.txt log=y
    
    from root directory.
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
        block_list = list()
        if len(argv) > 2:
            out_path = argv[2]
            if os.path.isdir(out_path):
                print('Writing output to', out_path)
            else:
                create = input(out_path + ' does not exist. Create? [y|n]')
                if create == 'y':
                    os.mkdir(out_path)

        save_log = False
        if len(argv) > 3:
            print("Reading block list from...", argv[3])
            with open(argv[3], 'r') as block_file:
                line = block_file.readline()
                while line:
                    line = line.strip()
                    block_list.append(line)
                    line = block_file.readline()
            if 'log=y' in argv[3:]:
                save_log = True
        anonymizer = ano.MailAnonymizer(None, block_list)
        list_len = len(file_list)
        count = 1
        # For later debugging reasons it's a good idea to save an error log.
        error_log = list()
        for file in file_list:
            # TODO: Converting mails currently can produce UnicodeEncodeError
            # and ValueError exceptions. This should be fixed someday. Unitl
            # then we need to deal with these exceptions in a defined way
            # without interrupting the whole script.
            print('[{0}|{1}] Processing {2}'.format(count, list_len, file))
            try:
                message = mailIo.readMailFromEmlFile(file)
                extMessage = exm.ExtentedEmailMessage(message)
                extMessage.extract_payload()
                anonymizer.extended_mail = extMessage
                anonymizer.anonymize()
                out_file = os.path.join(out_path, os.path.split(file)[1])
                # Writing and parsing the mail after anonymization will
                # sometimes throw the exception
                mailIo.writeMessageToEml(extMessage.email_message, out_file)
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
            if save_log is True:
                log_path = os.path.join(out_path, 'error_log.txt')
                with open(log_path, 'w') as log_file:
                    log_file.writelines(error_log)
    else:
        print("Path was not given")


if __name__ == "__main__":
    main()
