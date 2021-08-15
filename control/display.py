#!/usr/bin/env python3

import os
import subprocess
import time
import control
import digital_photo_frame as dpf

MODE = 'display'


def display():
    control.register_shutdown_handler()
    control.enter_mode(MODE, display_with_context)


def display_with_context(mode, config, database):
    dpf.setup_logging(dpf.SCRIPT_DIR / 'log.txt')
    dpf.setup_screen('admin')
    settings = dpf.SettingsDatabase(
        database, dpf.NextcloudFileLocator(check_validity=True))
    file_manager = dpf.FileManager(settings)
    displayer = dpf.Displayer(file_manager)
    displayer.start()


if __name__ == '__main__':
    display()
