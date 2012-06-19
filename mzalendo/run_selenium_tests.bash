#!/bin/bash

# abort on any error
set -e

find . -name '*.pyc' -delete

# run our tests
./manage.py test --selenium-only \
  core                           \
  feedback                       \
  user_profile                   \
  # comments2                      \
