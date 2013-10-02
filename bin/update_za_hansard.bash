#!/bin/bash

# abort on any errors
set -e

# check that we are in the expected directory
cd `dirname $0`/..

./bin/run_management_command_capture_stdout hansard_check_for_new_sources
./bin/run_management_command_capture_stdout hansard_run_parsing
./bin/run_management_command_capture_stdout hansard_load_into_sayit
