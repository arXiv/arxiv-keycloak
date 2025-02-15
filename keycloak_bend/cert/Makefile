.PHONY: upload-db-certs

# op item list --account arxiv.1password.com | awk -e '/dev auth db/ {print $1}'
DEV_AUTH_DB_ITEM_ID := bcoicp62oiepvqggwpj5f7lury

all: upload-db-certs

upload-db-certs: dev-authdb-db-certs-expand.sh

dev-authdb-db-certs-expand.sh: dev-authdb-client-cert.pem dev-authdb-client-key.pem dev-authdb-server-ca.pem
	PREFIX=dev-authdb- ./assemble-db-certs.sh

dev-authdb-client-cert.pem:
	./op-get-file.sh ${DEV_AUTH_DB_ITEM_ID} client-cert.pem dev-authdb-client-cert.pem

dev-authdb-client-key.pem:
	./op-get-file.sh ${DEV_AUTH_DB_ITEM_ID} client-key.pem dev-authdb-client-key.pem

dev-authdb-server-ca.pem:
	./op-get-file.sh ${DEV_AUTH_DB_ITEM_ID} server-ca.pem dev-authdb-server-ca.pem
