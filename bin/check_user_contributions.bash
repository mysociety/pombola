#!/bin/bash

# abort on any errors
set -e

# check that we are in the expected directory
cd `dirname $0`/..

source ../pombola-virtualenv/bin/activate

# This will print out to STDOUT if there are any. This should then get emailed to
# the right people by the cron script.

./manage.py feedback_report_pending
