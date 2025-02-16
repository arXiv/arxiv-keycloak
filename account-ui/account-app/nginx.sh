#!/bin/sh
mkdir -p /usr/share/nginx/html/user
cat > /usr/share/nginx/html/user/env-config.json <<EOF
{
  "AAA_URL": "${AAA_URL}",
  "ADMIN_API_BACKEND_URL": "${ADMIN_API_BACKEND_URL}",
  "ACCOUNT_UI_APP_ROOT": "${ACCOUNT_UI_APP_ROOT}"
}
EOF

nginx -g 'daemon off;'
