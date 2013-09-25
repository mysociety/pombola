#!/bin/bash

find . -name '*.pyc' -delete

coverage erase

OMIT="$(python -c 'import sys; print sys.prefix')/*"

coverage run --omit=$OMIT ./manage.py test   \
    core           \
    feedback       \
    hansard        \
    images         \
    scorecards     \
    search         \
    tasks

coverage run --append --omit=$OMIT ./manage.py test --selenium-only \
  core                           \
  feedback

coverage html -d pombola-coverage
