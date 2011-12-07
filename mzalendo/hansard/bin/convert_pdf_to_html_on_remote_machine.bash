#!/bin/bash

set -e

# This script allows you to run the PDF to HTML conversion on a remote machine.
# The reason is that pdftohtml on Mac (via homebrew) is too recent and buggy -
# whereas the older one available on Demian is just right.

# This script creates a tmp file on the remote machine, scps across the file to
# convert and then spits back the HTML over stdout

# To use this script instead of doing the conversion on the local machine put a
# value in the KENYA_PARSER_PDF_TO_HTML_HOST setting.

REMOTE=$1
FILE=$2

# echo "Convert $2 on $1"

TMP_PDF_FILE=`ssh $REMOTE tempfile -s .pdf`

# echo TMP_PDF_FILE $TMP_PDF_FILE

scp $FILE $REMOTE:$TMP_PDF_FILE

ssh $REMOTE pdftohtml -noframes -stdout $TMP_PDF_FILE

ssh $REMOTE rm $TMP_PDF_FILE

