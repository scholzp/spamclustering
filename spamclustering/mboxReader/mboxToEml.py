import hashlib
import mailbox
import os
import re

from datetime import datetime
from ..mailIo import mailIo


def generateMailId(message):
    """Generates an ID for use in the files name.

    :param message: Message to generate the ID from.
    :type message: :class:`email.message.Message`
    :return: ID generated from the mail.
    :rtype: str
    """
    mailId = str(message['Message-ID']).encode('ascii')
    hashOfId = ''
    if not mailId:
        return None

    mailTo = str(message['To']).encode('ascii')
    if not mailTo:
        return None

    hashOfId = hashlib.md5(mailId + mailTo).hexdigest()

    return hashOfId


def generateEmlFileName(message):
    """Generate a file name from a given message

    :param message: Message to process
    :type message: :class:`email.message.Message`
    :return: File name generated form the email.
    :rtype: str
    """
    id = generateMailId(message)
    inputFormat = '%a, %d %b %Y %H:%M:%S %z'
    if (not message['Date']) or (not id):
        return None
    mailDate = message['Date']
    regexp = re.compile(' \(.+\)')
    mailDate = re.sub(regexp, '', mailDate)
    mailDate = datetime.strptime(mailDate, inputFormat)
    date = mailDate.strftime('%Y-%m-%d-%H:%M:%S')

    return date+'_'+id+'.eml'


def processMbox(inPath, outPath):
    """Read the input of an MBox file and extract it. Write the extracted
    E-Mails to the given path.

    :param inPath: Path of the MBox file to extract.
    :type inPath: str
    :param outPath: Path to write the extracted E-Mails to.
    :type outPath: str
    """
    (_, tail) = os.path.split(inPath)
    (_, dirName) = os.path.split(tail)
    outDir = outPath + '/' + dirName
    if os.path.exists(outDir):
        if not os.path.isdir(outDir):
            print("Error:", outDir, " already exists, but isn't directory!")
            print("       Aborting...")
            return -1
        else:
            print("Warning: Using already existing directory", outDir)
    else:
        print("Create ", outDir)
        os.makedirs(outDir)

    for message in mailbox.mbox(inPath):
        fn = generateEmlFileName(message)
        fn = outDir + '/' + fn
        mailIo.writeMessageToEml(message, fn)
