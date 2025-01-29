#! /bin/sh
curl -X POST "http://localhost:21501/realms/arxiv/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=arxiv-user-migration" \
  -d "client_secret=f3dc975132f09b27d90f" \
  -d "username=reader" \
  -d "password=changeme" \
  -d "grant_type=password"
