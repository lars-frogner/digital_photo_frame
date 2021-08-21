import sys
import os
import logging
import re
import pathlib
import datetime
import time
import subprocess
from inotify.adapters import Inotify
from inotify.constants import IN_MODIFY, IN_CLOSE

SCRIPT_DIR = pathlib.Path(os.path.dirname(os.path.realpath(__file__)))


def setup_logging(filename, level=logging.INFO):
    logging.basicConfig(level=level,
                        filename=filename,
                        format='%(asctime)s: %(message)s')


def log_info(message):
    logging.info('INFO: %s', message)


def log_error(message, abort=False):
    logging.error('ERROR: %s', message)
    if abort:
        sys.exit(1)


def setup_screen(username):
    os.environ['DISPLAY'] = ':0'
    os.environ['XAUTHORITY'] = f'/home/{username}/.Xauthority'
    if 'HOME' not in os.environ:
        os.environ['HOME'] = '/home/{username}'


class Time:
    def __init__(self, day, month, year):
        self.day = day
        self.month = month
        self.year = year

    @staticmethod
    def any():
        return Time(None, None, None)

    @staticmethod
    def from_string(time_string):
        if time_string == 'any':
            return any()
        parts = re.split(r'\.|\/', time_string)
        if len(parts) == 1:
            return Time(None, None, int(parts[0]))
        elif len(parts) == 2:
            return Time(None, int(parts[0]), int(parts[1]))
        elif len(parts) == 3:
            return Time(int(parts[0]), int(parts[1]), int(parts[2]))
        else:
            log_error(f'Invalid format for time string {time_string}.',
                      abort=True)

    def includes(self, date):
        return (self.year is None or date.year == self.year) and (
            self.month is None or date.month
            == self.month) and (self.day is None or date.day == self.day)

    def __eq__(self, other):
        return isinstance(
            other, self.__class__
        ) and other.year == self.year and other.month == self.month and other.day == self.day

    def __ne__(self, other):
        return not isinstance(
            other, self.__class__
        ) or other.year != self.year or other.month != self.month or other.day != self.day

    def __le__(self, other):
        if self.year is None or other.year is None or self.year < other.year:
            return True
        elif self.year == other.year:
            if self.month is None or other.month is None or self.month < other.month:
                return True
            elif self.month == other.month:
                if self.day is None or other.day is None or self.day <= other.day:
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False

    def __ge__(self, other):
        if self.year is None or other.year is None or self.year > other.year:
            return True
        elif self.year == other.year:
            if self.month is None or other.month is None or self.month > other.month:
                return True
            elif self.month == other.month:
                if self.day is None or other.day is None or self.day >= other.day:
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False

    def __repr__(self):
        return '{}{}{}'.format(
            '' if self.day is None else f'{self.day:02d}.',
            '' if self.month is None else f'{self.month:02d}.',
            'any' if self.year is None else f'{self.year:d}')


class TimePeriod:
    def __init__(self, start_time, end_time):
        self.start_time = start_time
        self.end_time = end_time

    @staticmethod
    def string_is_valid(string):
        return len(string.split('-')) == 2

    @staticmethod
    def from_string(time_period_string):
        start_time_string, end_time_string = tuple(
            map(str.strip, time_period_string.split('-')))
        return TimePeriod(Time.from_string(start_time_string),
                          Time.from_string(end_time_string))

    @staticmethod
    def from_strings(start_time_string, end_time_string):
        return TimePeriod(Time.from_string(start_time_string),
                          Time.from_string(end_time_string))

    def includes(self, date):
        return self.start_time <= date and self.end_time >= date

    def __eq__(self, other):
        return isinstance(
            other, self.__class__
        ) and other.start_time == self.start_time and other.end_time == self.end_time

    def __ne__(self, other):
        return not isinstance(
            other, self.__class__
        ) or other.start_time != self.start_time or other.end_time != self.end_time

    def __repr__(self):
        return f'{self.start_time} - {self.end_time}'


class TimePeriods:
    def __init__(self, *time_strings):
        if 'any' in time_strings:
            self.times = [Time.any()]
        else:
            self.times = list(
                map(
                    lambda time_string: TimePeriod.from_string(time_string)
                    if TimePeriod.string_is_valid(time_string) else Time.
                    from_string(time_string), time_strings))

    @staticmethod
    def any():
        return TimePeriods('any')

    def includes(self, date):
        return len(list(filter(lambda time: time.includes(date),
                               self.times))) > 0

    def __eq__(self, other):
        return isinstance(other, self.__class__) and len(other.times) == len(
            self.times) and all(
                (a == b for a, b in zip(self.times, other.times)))

    def __ne__(self, other):
        return not isinstance(other, self.__class__) or len(
            other.times) != len(self.times) or any(
                (a != b for a, b in zip(self.times, other.times)))

    def __repr__(self):
        return ", ".join(map(str, self.times))


ANY_TIME_PERIOD = TimePeriods.any()


class StandardFileLocator:
    def __init__(self, check_validity=True):
        self.check_validity = check_validity

    def generate_valid_path(self, path):
        if self.check_validity and not path.is_dir():
            log_error(
                f'Image path \'{path}\' does not point to a valid directory.')
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
            log_error(
                f'Image path \'{valid_path}\' does not point to a valid directory.'
            )
            return None
        return valid_path


class Settings:
    def __init__(self,
                 file_locator,
                 default_folders=None,
                 default_times=ANY_TIME_PERIOD,
                 default_delay=10,
                 default_randomize=False,
                 default_feh_flags=[
                     '--preload', '--borderless', '--fullscreen',
                     '--auto-zoom', '--auto-rotate', '--hide-pointer'
                 ]):
        self._file_locator = file_locator

        self.default_folders = default_folders
        self.default_times = default_times
        self.default_delay = default_delay
        self.default_randomize = default_randomize

        self._default_feh_flags = default_feh_flags

        self._folders = default_folders
        self._times = default_times
        self._delay = default_delay
        self._randomize = default_randomize

        self._change_flags = {'any': False}

        self._time_text_re = re.compile(
            r'(any|((?:\d\d?[\.\/])?(?:\d\d?[\.\/])?(?:\d{4})(?:\s*-\s*(?:\d\d?[\.\/])?(?:\d\d?[\.\/])?(?:\d{4}))?))',
            flags=re.IGNORECASE)

    @property
    def file_locator(self):
        return self._file_locator

    @property
    def folders(self):
        return self._folders

    @property
    def delay(self):
        return self._delay

    @property
    def times(self):
        return self._times

    @property
    def randomize(self):
        return self._randomize

    @property
    def changed(self):
        return self.get_change_flag('any')

    @property
    def feh_delay_arguments(self):
        return ['--slideshow-delay', f'{self.delay}']

    @property
    def feh_randomize_arguments(self):
        return ['--randomize'] if self.randomize else []

    @property
    def feh_arguments(self):
        return self._default_feh_flags + self.feh_delay_arguments + self.feh_randomize_arguments

    def _parse_settings(self, resource):
        folders = self._parse_folders(resource)
        if folders != self.folders:
            self._folders = folders
            self._register_change('folders')
            log_info(f'Using folders: {", ".join(map(str, self.folders))}.')

        times = self._parse_times(resource)
        if times != self.times:
            self._times = times
            self._register_change('times')
            log_info(f'Using time periods: {self.times}.')

        delay = self._parse_delay(resource)
        if delay != self.delay:
            self._delay = delay
            self._register_change('delay')
            log_info(f'Using delay: {self.delay:g} s.')

        randomize = self._parse_randomize(resource)
        if randomize != self.randomize:
            self._randomize = randomize
            self._register_change('randomize')
            log_info(f'Using randomize: {self.randomize}')

    def _process_folders_text(self, folders_text, error_message=None):
        folder_strings = map(str.strip, folders_text.split(','))
        folder_paths = map(pathlib.Path, folder_strings)

        valid_paths = list(
            filter(None,
                   map(self.file_locator.generate_valid_path, folder_paths)))
        if not valid_paths:
            if error_message is not None:
                log_error(error_message)
            return self.folders

        return valid_paths

    def _process_times_text(self, time_text, error_message=None):
        matches = [match[0] for match in self._time_text_re.findall(time_text)]
        if not matches:
            if error_message is not None:
                log_error(error_message)
            return self.times
        return TimePeriods(*matches)

    def get_change_flag(self, flag):
        return self._change_flags.get(flag, False)

    def reset_change_flags(self):
        for flag in self._change_flags:
            self._change_flags[flag] = False

    def _register_change(self, flag):
        self._change_flags[flag] = True
        self._change_flags['any'] = True


class SettingsFile(Settings):
    def __init__(self, file_path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._file_path = pathlib.Path(file_path)

        self._folder_re = re.compile(r'^folders:(.+)$',
                                     flags=re.MULTILINE | re.IGNORECASE)

        self._time_re = re.compile(r'^time:(.+)$',
                                   flags=re.MULTILINE | re.IGNORECASE)

        self._delay_re = re.compile(r'^delay:\s*([0-9]+(?:\.[0-9]+)?)\s*$',
                                    flags=re.MULTILINE | re.IGNORECASE)

        self._randomize_re = re.compile(r'random(?:i[sz]e)?\s*$',
                                        flags=re.MULTILINE | re.IGNORECASE)

    @property
    def file_path(self):
        return self._file_path

    def read_settings(self):
        if not self.file_path.is_file():
            log_error(f'Config file \'{self.file_path}\' does not exist.',
                      abort=True)
        with open(self.file_path, 'r') as f:
            text = f.read()

        self._parse_settings(text)

    def _parse_folders(self, text):
        match = self._folder_re.search(text)
        if not match:
            log_error(f'No \'folders\' entry in {self.file_path}.')
            return self.folders
        folders_text = match[1]

        return self._process_folders_text(
            folders_text,
            error_message=
            f'No valid folders specified in \'folders\' entry in {self.file_path}.'
        )

    def _parse_times(self, text):
        match = self._time_re.search(text)
        if not match:
            log_error(f'No valid \'time\' entry in {self.file_path}.')
            return self.times

        return self._process_times_text(
            match[1],
            error_message=f'No valid \'time\' entry in {self.file_path}.')

    def _parse_delay(self, text):
        match = self._delay_re.search(text)
        if not match:
            log_error(f'No valid \'delay\' entry in {self.file_path}.')
            return self.delay
        delay = float(match[1])
        return delay

    def _parse_randomize(self, text):
        if self._randomize_re.search(text):
            return True
        else:
            return False


class SettingsDatabase(Settings):
    def __init__(self, database, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._database = database
        self._table_name = 'display_settings'

    def read_settings(self):
        with self._database as database:
            self._parse_settings(database)

    def _parse_folders(self, database):
        folders_text = database.read_values_from_table(self._table_name,
                                                       'folders')
        if folders_text is None:
            return None
        return self._process_folders_text(
            ','.join(folders_text.split('\n')),
            error_message=
            f'No valid folders specified in \'folders\' entry in database {self._database.name}.'
        )

    def _parse_times(self, database):
        times_text = database.read_values_from_table(self._table_name, 'times')
        if times_text is None:
            return None
        return self._process_times_text(
            ','.join(times_text.split('\n')),
            error_message=
            f'No valid \'times\' entry in database {self._database.name}.')

    def _parse_delay(self, database):
        delay = database.read_values_from_table(self._table_name, 'delay')
        if delay is None:
            return self.delay
        else:
            return float(delay)

    def _parse_randomize(self, database):
        randomize = database.read_values_from_table(self._table_name,
                                                    'randomize')
        if randomize is None:
            return self.randomize
        else:
            return bool(randomize)


class FileManager:
    def __init__(self, settings):
        self._settings = settings
        self.settings.read_config()
        self.settings.reset_change_flags()

        self._file_list_path = SCRIPT_DIR / '.filelist.txt'

        self._file_times = {}
        self._all_file_times = {}
        self._update_file_times()

        self._filtered_file_times = {}
        self._update_filtered_file_times()

        self.update_file_list()

    @property
    def settings(self):
        return self._settings

    @property
    def file_list_path(self):
        return self._file_list_path

    @property
    def feh_arguments(self):
        return self.settings.feh_arguments + ['-f', str(self.file_list_path)]

    def reread_settings(self):
        self.settings.read_settings()
        if self.settings.get_change_flag('folders'):
            self._update_file_times()
        if self.settings.get_change_flag('times'):
            self._update_filtered_file_times()
        self.settings.reset_change_flags()

    def update_file_list(self):
        with open(self.file_list_path, 'w') as f:
            f.write('\n'.join(self._file_times.keys()))

    def _obtain_filename_list(self):
        filename_list = subprocess.check_output([
            SCRIPT_DIR / 'find_image_files.sh',
            *list(map(str, self.settings.folders))
        ],
                                                text=True).split('\n')[:-1]
        return filename_list

    def _update_file_times(self):
        filename_list = self._obtain_filename_list()

        new_filenames_list = []
        existing_filnames_list = []
        for filename in filename_list:
            if filename in self._all_file_times:
                existing_filnames_list.append(filename)
            else:
                new_filenames_list.append(filename)

        self._file_times = dict(
            filter(lambda item: item[0] in existing_filnames_list,
                   self._file_times.items()))

        log_info(f'Adding {len(new_filenames_list)} new files.')
        new_times_list = subprocess.check_output(
            [SCRIPT_DIR / 'find_image_times.sh', *new_filenames_list],
            text=True).split('\n')[:-1]
        for new_filename, new_time_string in zip(new_filenames_list,
                                                 new_times_list):
            splitted = new_time_string.split()
            if splitted[1][:2] == '24':
                new_time_string = '{} {}'.format(splitted[0],
                                                 '00' + splitted[1][2:])
            self._file_times[new_filename] = datetime.datetime.fromisoformat(
                new_time_string)
            self._all_file_times[new_filename] = self._file_times[new_filename]

    def _update_filtered_file_times(self):
        self._filtered_file_times = dict(
            filter(lambda item: self.settings.times.includes(item[1]),
                   self._file_times.items()))


class Displayer:
    def __init__(self, file_manager):
        self._file_manager = file_manager

        self._process = None

    @property
    def file_manager(self):
        return self._file_manager

    def __enter__(self):
        self._start()
        return self

    def __exit__(self, *args):
        self._stop()

    def wait(self):
        if self._process is None:
            return
        while self._process.poll() is None:
            time.sleep(0.1)
        if self._process.returncode == 0:
            return
        else:
            raise RuntimeError(
                f'feh exited with error code {self._process.returncode}')

    def _start(self):
        self._stop()
        self._process = subprocess.Popen(
            ['feh', *self.file_manager.feh_arguments])

    def _stop(self):
        if self._process is not None:
            self._process.terminate()
            self._process = None


if __name__ == "__main__":
    setup_logging(SCRIPT_DIR / 'log.txt')
    setup_screen('admin')
    settings = SettingsFile(SCRIPT_DIR / 'frame_config.txt',
                            NextcloudFileLocator(check_validity=True))
    file_manager = FileManager(settings)
    with Displayer(file_manager) as displayer:
        displayer.wait()

    # notifier = Inotify(block_duration_s=1)
    # notifier.add_watch(str(settings.file_path), mask=(IN_MODIFY | IN_CLOSE))

    # for event in notifier.event_gen(yield_nones=False):
    #     file_manager.reread_settings()
