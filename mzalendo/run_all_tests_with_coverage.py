#!/bin/bash

find . -name '*.pyc' -delete

coverage erase

OMIT="$(python -c 'import sys; print sys.prefix')/*"

coverage run --omit=$OMIT ./manage.py test   \
    core           \
    feedback       \
    hansard        \
    helpers        \
    images         \
    info           \
    scorecards     \
    search         \
    tasks          \
    user_profile

coverage run --omit=$OMIT ./manage.py test --selenium-only \
  core                           \
  feedback                       \
  user_profile

coverage html -d pombola-coverage
