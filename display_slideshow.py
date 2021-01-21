import sys
import os
import logging
import re
import pathlib
import subprocess
from inotify.adapters import Inotify
from inotify.constants import IN_MODIFY, IN_CLOSE

SCRIPT_PATH = pathlib.Path(os.path.dirname(os.path.realpath(__file__)))

CONFIG_FILE_PATH = SCRIPT_PATH / 'frame_config.txt'
LOG_FILE_PATH = SCRIPT_PATH / 'log.txt'

logging.basicConfig(level=logging.INFO,
                    filename=LOG_FILE_PATH,
                    format='%(asctime)s: %(message)s')


def log_info(message):
    logging.info('INFO: %s', message)


def log_error(message, abort=False):
    logging.error('ERROR: %s', message)
    if abort:
        sys.exit(1)


class StandardFileLocator:
    def __init__(self, check_validity=True):
        self.check_validity = check_validity

    def generate_valid_path(self, path):
        if self.check_validity and not path.is_dir():
            log_error('Image path \'{}\' does not point to a valid directory.'.
                      format(path))
            return None
        return path


class NextcloudFileLocator:
    def __init__(self, base_path='/mnt/hdd1', check_validity=True):
        self.base_path = base_path
        self.check_validity = check_validity

    def generate_valid_path(self, path):
        user = path.parts[0]
        valid_path = pathlib.Path(self.base_path, user, 'files',
                                  *path.parts[1:])
        if self.check_validity and not valid_path.is_dir():
            log_error('Image path \'{}\' does not point to a valid directory.'.
                      format(valid_path))
            return None
        return valid_path


class Config:
    def __init__(self,
                 file_locator,
                 file_path=CONFIG_FILE_PATH,
                 default_folders=None,
                 default_delay=10):
        self._file_locator = file_locator
        self._file_path = pathlib.Path(file_path)

        self._folders = default_folders
        self._delay = default_delay
        self._changed = False

        self._folder_re = re.compile(r'^folders:(.+)$', flags=re.MULTILINE)
        self._delay_re = re.compile(r'^delay:\s*([0-9]+(?:\.[0-9]+)?)\s*$',
                                    flags=re.MULTILINE)

        self._default_feh_flags = [
            '--preload', '--borderless', '--fullscreen', '--auto-zoom',
            '--auto-rotate', '--hide-pointer'
        ]

    @property
    def file_locator(self):
        return self._file_locator

    @property
    def file_path(self):
        return self._file_path

    @property
    def folders(self):
        return self._folders

    @property
    def delay(self):
        return self._delay

    @property
    def changed(self):
        return self._changed

    def create_file_list(self):
        output = subprocess.check_output([
            SCRIPT_PATH / 'find_image_files_with_times.sh',
            *list(map(str, self.folders))
        ],
                                         text=True)
        print(output)

    def parse_file(self):
        if not self.file_path.is_file():
            log_error('Config file \'{}\' does not exist.'.format(
                self.file_path),
                      abort=True)
        with open(self.file_path, 'r') as f:
            text = f.read()

        folders = self._parse_folders(text)
        if folders != self.folders:
            self._folders = folders
            self._changed = True
        log_info('Using folders: {}.'.format(', '.join(map(str,
                                                           self.folders))))

        print(self.folders)

        delay = self._parse_delay(text)
        if delay != self.delay:
            self._delay = delay
            self._changed = True
        log_info('Using a delay of {:g} s.'.format(self.delay))

        print(self.delay)

    def _parse_folders(self, text):
        match = self._folder_re.search(text)
        if not match:
            log_error('No \'folders\' entry in {}.'.format(self.file_path))
            return None
        folders_text = match[1]

        folder_strings = map(str.strip, folders_text.split(','))
        folder_paths = map(pathlib.Path, folder_strings)

        valid_paths = list(
            filter(None,
                   map(self.file_locator.generate_valid_path, folder_paths)))
        if not valid_paths:
            log_error('No valid folders specified in \'folders\' entry in {}.'.
                      format(self.file_path))
            return None

        return valid_paths

    def _parse_delay(self, text):
        match = self._delay_re.search(text)
        if not match:
            log_error('No valid \'delay\' entry in {}.'.format(self.file_path))
            return None
        delay = float(match[1])
        return delay


if __name__ == "__main__":

    config = Config(NextcloudFileLocator(check_validity=True))

    notifier = Inotify(block_duration_s=1)
    notifier.add_watch(str(config.file_path), mask=(IN_MODIFY | IN_CLOSE))

    #for event in notifier.event_gen(yield_nones=False):
    config.parse_file()
    config.create_file_list()
