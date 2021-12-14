# Makefile

include .lily/lily_assistant.makefile
include .lily/lily.makefile

#
# Postgres
#
.PHONY: create_postgres
create_postgres:  ## create dockerized postgres server
	export POSTGRES_PASSWORD=mysecret && \
	export POSTGRES_HOST=localhost && \
	export POSTGRES_PORT=5435 && \
	docker run -d --name lily-postgres \
		--env-file <(env | grep POSTGRES) \
		-p 5435:5432 \
		postgres

.PHONY: create_postgres_dbs
create_postgres_dbs:
	docker exec -u postgres -ti lily-postgres psql -c "create role lily with login password 'mysecret';" && \
	docker exec -u postgres -ti lily-postgres psql -c "GRANT ALL ON SCHEMA public to lily;" && \
	docker exec -u postgres -ti lily-postgres psql -c "ALTER USER lily CREATEDB;" && \
	docker exec -u postgres -ti lily-postgres createdb -O lily lily

.PHONY: start_postgres
start_postgres:  ## start dockerized postgres server
	docker start lily-postgres

.PHONY: stop_postgres
stop_postgres:   ## stop dockerized postgres server
	docker stop lily-postgres
