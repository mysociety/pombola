#!/bin/bash

# abort on any error
set -e

# run our tests
./manage.py test --selenium-only

