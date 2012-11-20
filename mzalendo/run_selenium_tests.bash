#!/bin/bash

# abort on any error
set -e

find . -name '*.pyc' -delete

# run our tests
coverage run ./manage.py test --selenium-only \
  core                           \
  feedback                       \
  user_profile                   
