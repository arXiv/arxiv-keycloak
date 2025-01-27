#! /bin/sh
curl -X POST "http://localhost:21501/realms/arxiv/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=arxiv-user-migration" \
  -d "client_secret=9RVzIW1VQpYGDB0kqgpZDkGChW9ly28c" \
  -d "username=reader" \
  -d "password=changeme" \
  -d "grant_type=password"
