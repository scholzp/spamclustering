import email
import os


def writeMessageToEml(message, fn):
    """Use :class:`email.generator.Generator` to write the given message to the
    respective path.
    :params message: Message to write to the path.
    :type message: :class:`email.message.Message`
    :params fn: Path to write the message to. Must be a legit path.
    :type fn: str
   """
    if fn and fn != '':
        with open(fn, 'w') as out:
            gen = email.generator.Generator(out)
            gen.flatten(message)


def readMailFromEmlFile(path):
    """Return an EmailMessage object obtained from a file.

    :param path: Path to a eml file to read.
    :type path: str
    :returns: Message generated from the file.
    :rtype: :class:`email.message.Message`
    """
    result = None
    if os.path.isfile(path):
        with open(path, 'r') as fp:
            # Use policy.default for creating a EmailMessage factory instead of
            # a message factory
            mail_parser = email.parser.Parser(policy=email.policy.default)
            message = mail_parser.parse(fp)
            result = message
    else:
        print("Error: File does not exists!")
    return result
