#!/bin/bash

source "$(dirname "${BASH_SOURCE[0]}")/../.env"

cd "$(dirname "${BASH_SOURCE[0]}")/../src"

export CLASSIC_DB_URI=mysql://arxiv:arxiv_password@127.0.0.1:$ARXIV_DB_PORT/arXiv
export SQLALCHEMY_RECORD_QUERIES=true
export API_SECRET_KEY="$LEGACY_AUTH_API_TOKEN"

PORT=${PORT:-$LEGACY_AUTH_PORT}
uvicorn legacy_auth_provider:app --port $PORT --log-config logging.conf
