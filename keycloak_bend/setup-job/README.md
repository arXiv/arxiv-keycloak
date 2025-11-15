# Keycloak Setup Job

Docker container for Cloud Run Job that configures Keycloak realm.

## What It Does

1. Waits for Keycloak to be ready
2. Fetches realm config from Secret Manager
3. Configures realm via Admin API (roles, scopes, clients, etc.)

## Files

- `Dockerfile` - Container definition
- `requirements.txt` - Python dependencies
- `setup_realm_job.py` - Main script (health check + Secret Manager fetch)
- `../tools/setup_arxiv_realm.py` - Core setup logic

## Building

**Automated:** GitHub Actions builds on push to `master`

**Manual:**
```bash
docker build -t gcr.io/arxiv-development/arxiv-keycloak/keycloak-setup:latest -f Dockerfile ..
docker push gcr.io/arxiv-development/arxiv-keycloak/keycloak-setup:latest
```

## Environment Variables

**Required:**
- `KC_URL` - Keycloak URL
- `KC_ADMIN_PASSWORD` - Admin password
- `ARXIV_USER_SECRET` - OAuth2 client secret
- `REALM_CONFIG_SOURCE` - `secret://projects/PROJECT/secrets/NAME/versions/latest` or `file:///path/to/realm.json`

**Optional:**
- `LEGACY_AUTH_API_TOKEN` - Legacy auth token
- `LEGACY_AUTH_URI` / `URI` - Legacy auth provider URI
- `REALM_NAME` - Realm name (default: `arxiv`)
- `KEYCLOAK_WAIT_TIMEOUT` - Wait timeout seconds (default: 600)
- `KEYCLOAK_WAIT_INTERVAL` - Retry interval seconds (default: 5)

## Running Locally

```bash
docker run --rm --network host \
  -e KC_URL="http://localhost:3033" \
  -e KC_ADMIN_PASSWORD="admin" \
  -e ARXIV_USER_SECRET="test" \
  -e LEGACY_AUTH_API_TOKEN="test" \
  -e REALM_CONFIG_SOURCE="file:///app/realm.json" \
  -v $(pwd)/../realms/arxiv-realm-localhost.json:/app/realm.json \
  keycloak-setup:local
```

## Running on Cloud Run

See `terraform/keycloak-setup/README.md`

```bash
gcloud run jobs execute keycloak-realm-setup-ENV --region REGION --project PROJECT --wait
```
