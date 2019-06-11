from __future__ import print_function

import os
from os.path import abspath, realpath, join, dirname
import re
import sys

import yaml

base_dir = abspath(join(dirname(realpath(__file__)), '..'))

def env_value_to_python(s):
    if s.lower() == 'true':
        return True
    elif s.lower() == 'false':
        return False
    # Look for plain integers (positive or negative):
    m = re.search(r'^-?\d+$', s)
    if m:
        return int(m.group(0), 10)
    # Otherwise assume this really is a string:
    return s

config_path = None
if os.environ.get('CONFIG_FROM_ENV'):
    general_yml_example_fname = join(base_dir, 'conf', 'general.yml-example')
    with open(general_yml_example_fname) as f:
        example_config = yaml.safe_load(f)
    config = {
        k: env_value_to_python(os.environ[k])
        for k in example_config.keys()
        if k in os.environ
    }
else:
    config_path =  join(base_dir, 'conf', 'general.yml')
    with open(config_path) as f:
        config = yaml.safe_load(f)
