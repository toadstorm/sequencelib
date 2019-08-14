"""
sequencelib by henry foster, henry@toadstorm.com
A library of tools for collating and manipulating sequences of files.
"""



import os
import re
import decimal
import copy

SEQUENCE_REGEX = '^(\D+[._])(\d+\.?\d*)([._]?\w*)\.(\w{2,5})$'
# capture groups: (prefix) (number) (optional suffix) (file extension)

def drange(x, y, jump):
    """
    like range(), but with Decimal objects instead.
    :param x: the start of the range.
    :param y: the end of the range.
    :param jump: the step.
    :return: a Generator that returns each value in the range, one at a time.
    """
    while x < y:
        yield float(x)
        x += decimal.Decimal(jump)


class File(object):
    """
    A generic class to contain a file path and a number (the sequence order)
    """
    def __init__(self, file):
        self.number = 0
        self.path = file
        match = re.match(SEQUENCE_REGEX, file)
        if match:
            if match.groups()[1]:
                num = match.groups()[1].lstrip('0')
                self.number = decimal.Decimal(num)


class Sequence(object):
    """
    A class containing a list of File objects, and the prefix/suffix/extension
    for matching with other sequences or files.
    """
    def __init__(self, files=None):
        self._files = list()    # all File objects in this sequence
        self.prefix = ''        # the prefix (before the frame number)
        self.suffix = ''        # the suffix (after the frame number)
        self.extension = ''     # the file extension
        self.padding = 0        # the framepadding
        self.directory = ''     # the base directory this sequence lives in

        if files:
            # if the user provided a single file instead of a list of files, just convert it
            if isinstance(files, str):
                files = [files]
            self.directory = os.path.dirname(files[0])

            # parse the first file in the list to get prefix, suffix, extension, padding
            match = re.match(SEQUENCE_REGEX, os.path.basename(files[0]))
            if match:
                if match.groups()[0]:
                    self.prefix = match.groups()[0]
                if match.groups()[1]:
                    # check to see if there's padding in there.
                    zeroes = len(match.groups()[1]) - len(match.groups()[1].lstrip('0'))
                    self.padding = zeroes
                if match.groups()[2]:
                    self.suffix = match.groups()[2]
                if match.groups()[3]:
                    self.extension = match.groups()[3]

            # now convert each file into a File object and add it to our internal _files list
            for f in files:
                file_obj = File(f)
                self._files.append(file_obj)

            # sort by frame number
            self._files = sorted(self._files, key=lambda x: x.number)

    def append(self, filepath):
        """
        add a file (by path) to this Sequence.
        :param filepath: the full path on disk to the file.
        :return: None
        """
        file_obj = File(filepath)
        # screen the list of files first so we can't have duplicates.
        if self._files:
            for file in self._files:
                if file.path == filepath:
                    return
        self._files.append(file_obj)
        self._files = sorted(self._files, key=lambda x: x.number)

    def remove(self, filepath):
        """
        remove a file (by path) from this Sequence.
        :param filepath: the path to remove, or optionally, the File object to remove.
        :return: None
        """
        if isinstance(filepath, File):
            filepath = File.path
        if self._files:
            for file in self._files:
                if file.path == filepath:
                    self._files.remove(file)
                    break

    def files(self):
        """
        return a friendly list of file paths as strings (rather than File objects as in self._files)
        :return: a list of file paths as strings, in order.
        """
        if self._files:
            return [f.path for f in self._files]
        return None

    def file_match(self, file):
        """
        check to see if the given file matches this sequence.
        :param file: the file to test.
        :return: True if the file belongs in this sequence.
        """
        match = re.match(SEQUENCE_REGEX, file)
        if match:
            if match.groups():
                if match.groups()[0] == self.prefix and match.groups()[2] == self.suffix and match.groups()[3] == self.extension:
                    return True
        return False

    def find_missing_frames(self, step=1, start=None, end=None):
        """
        Ensure that the sequence is contiguous.
        :param step: the step between frames (defaults to 1)
        :param start: the start of the sequence. default is whatever the first detected frame is.
        :param end: the end of the sequence. default is whatever the last detected frame is.
        :return: a list of missing filenames, if any exist.
        """
        step = decimal.Decimal(step)
        if start is None:
            start = self._files[0].number
        if end is None:
            end = self._files[-1].number
        # copy our internal _files list to a temporary duplicate so we can remove from it as we test for files
        test_files = copy.deepcopy(self._files)
        missing_frames = list()
        # for each potential frame in our list, verify that a File with an identical number exists in the Sequence
        for frame in drange(start, end+step, step):
            found = False
            for file in test_files:
                if file.number == frame:
                    found = True
                    test_files.remove(file)
                    break
            if not found:
                missing_frames.append(decimal.Decimal(frame))

        if missing_frames:
            # create full file paths for these if possible and then return them so they're human-readable.
            missing_files = list()
            for frame in missing_frames:
                file = self.prefix + str(frame).zfill(self.padding) + self.suffix + '.' + self.extension
                filepath = os.path.join(self.directory, file).replace('\\', '/')
                missing_files.append(filepath)
            return missing_files
        return None

    def debug(self):
        """
        print a bunch of crap about the sequence.
        :return: None
        """
        print('Sequence has {} files.'.format(len(self._files)))
        print('Prefix: {}'.format(self.prefix))
        print('Suffix: {}'.format(self.suffix))
        print('Extension: {}'.format(self.extension))
        print('All files: {}'.format(self.files()))
        print('Missing files: {}'.format(self.find_missing_frames()))


def is_file_valid(file):
    """
    test if a file could actually be a sequence.
    :param file: the file path to test.
    :return: True if the file could be part of a sequence.
    """
    match = re.match(SEQUENCE_REGEX, file)
    if match:
        if match.groups()[1]:
            return True
    return False


def find_sequences(path, extensions=None):
    """
    given a path on disk, find all possible file sequences.
    :param path: the path to search.
    :param extensions: if provided, a list of file extensions to mask by.
    :return: a list of Sequence objects.
    """
    sequences = list()
    all_files = os.listdir(path)
    if not all_files:
        return None
    all_files = [f for f in all_files if not os.path.isdir(os.path.join(path,f))]
    if not all_files:
        return None
    if extensions:
        if isinstance(extensions, str):
            extensions = [extensions]
        extensions = [f.strip('.') for f in extensions]
        all_files = [f for f in os.listdir(path) if os.path.splitext(f)[-1].strip('.') in extensions]
        if not all_files:
            return None

    # collate found files into sequences if they fit the regex,
    for file in all_files:
        found_match = False
        if sequences:
            for seq in sequences:
                if seq.file_match(file):
                    found_match = True
                    seq.append(os.path.join(path, file).replace('\\', '/'))
                    break
        if not found_match:
            # generate a new sequence if this is a sequenceable file.
            if is_file_valid(file):
                new_seq = Sequence(os.path.join(path, file).replace('\\', '/'))
                sequences.append(new_seq)
    return sequences



