#!/bin/sh
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "$SCRIPT_DIR"
if [ ! -d venv ] ; then
  make
fi

. venv/bin/activate
export GOOGLE_APPLICATION_CREDENTIALS=/opt_arxiv/ntai/gcp/cit-gcp-dev-pubsub-sa.json
export INTERNAL_MTA=
python pubsub_to_email.py
deactivate
