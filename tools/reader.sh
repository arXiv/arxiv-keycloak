#!
curl -X POST "http://localhost:21501/realms/arxiv/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=arxiv-user-m2m" \
  -d "client_secret=djNvDFN7zjiDdj98dE0m9zMGIvImcsv7" \
  -d "username=reader" \
  -d "password=changeme" \
  -d "grant_type=password"
