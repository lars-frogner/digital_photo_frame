import os
import json
import pathlib

SCRIPT_DIR = pathlib.Path(os.path.dirname(os.path.realpath(__file__)))
CONFIG_PATH = SCRIPT_DIR / '..' / 'config' / 'config.json'


def read_config():
    with open(CONFIG_PATH, 'r') as f:
        config = json.loads(f.read())
    return config
