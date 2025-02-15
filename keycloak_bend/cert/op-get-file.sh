#!/usr/bin/env bash
ITEM_ID=$1
shift

OP_FILENAME=$1
shift

OUT_FILENAME=$1
shift

op item get --account arxiv.1password.com $ITEM_ID --format json | jq -r ".files[] | select(.name == \"$OP_FILENAME\") | .content_path" | awk -F / '{ print "op://"$4"/"$6"/"$8 }' | xargs op read --account arxiv.1password.com -o ./$OUT_FILENAME
