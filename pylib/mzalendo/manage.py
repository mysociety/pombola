#!/usr/bin/env python

# Do this so that the include paths are set up correctly
import setup_env
import settings

from django.core.management import execute_manager

if __name__ == "__main__":
    execute_manager(settings)
